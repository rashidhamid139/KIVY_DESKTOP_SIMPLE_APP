from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
import os, sys
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.config import Config
import json, re, datetime, pprint, requests, base64, pyodbc
from io import BytesIO
from tika import parser
from dateutil.parser import parse
import threading
import configparser
from kivy.uix.scrollview import ScrollView
import pandas as pd



class configfile(object):
    @property
    def configure_details(self):
        config = configparser.ConfigParser()
        os.chdir(os.environ['USERPROFILE'])
        config.read('configure.ini')
        return config

class Admin_Screen(Screen):
    pass
class Display(BoxLayout):
    pass


class Email_Screen(Screen):
    pass

class Database_Screen(Screen):
    pass
class Elasticsearch_Screen(Screen):
    pass
class Collection_Screen(Screen):
    pass
class Api_Screen(Screen):
    pass


class ButtonLabel(ButtonBehavior, Label):
    @property
    def selected_list_content(self):
        return App.get_running_app().root.ids.selected_list.ids.content

    @property
    def deselected_list_content(self):
        return App.get_running_app().root.ids.deselected_list.ids.content


    def change_location(self):

        if self.parent == self.selected_list_content:
            self.parent.remove_widget(self)
            self.deselected_list_content.add_widget(self)


        else:
            self.parent.remove_widget(self)
            self.selected_list_content.add_widget(self)

class CustomRecycleView(RecycleView):
    pass
class P(FloatLayout):
    pass
class MigrationWindow(BoxLayout, Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #self.es = Elasticsearch(['https://search-hitech-tuxhxhzzt4sw2d5sak3l6e2mny.ap-south-1.es.amazonaws.com/'])
        self.data = {}
        self.get_fields = {}
        self.check_subject = []
        self.check_email = []
        self.check_messageId = []
        self.flag=True

    def get_second_api_response(self, volumeID, uniqueID):
        url2 = 'http://archivalab.globalhuntindia.com:8090/api/v1/blobs/' + volumeID + '/' + uniqueID + '/'
        ss = requests.get(url2, headers={'authorization': 'Basic Uk9PVDphZG1pbjphZG1pbkAxMjM='})
        return json.loads(ss.text)

    def modify_get_second_api_response(self, a, b):
        self.data = {}
        resp = MigrationWindow.get_second_api_response(self, a, b)
        for i in range(len(resp)):
            self.data.update({resp[i]['field']: resp[i]['value']})

        check_list = ['mimetype', 'selfmessage', 'volid', 'thread', 'size', 'priority', 'body', 'attachsize',
                      'attachmentlist', 'parts']
        for val in check_list:
            try:
                del self.data[val]
            except:
                pass

    def cleaning_fields_function(self):
        unwanted_word = "#$%&\'()<=>\t\n\r\x0b\x0c"
        def get_mail(input1):
            if input1 != None:
                input1 = ''.join(filter(lambda x: x not in unwanted_word, iter(input1)))
                return (re.findall('\S+@\S+', input1))
            else:
                return None

        self.data['from'] = get_mail(self.data['from'])[0]
        self.data['to'] = get_mail(self.data.get('to'))
        try:
            self.data['attachname'] = self.data['Attach_name']
            del self.data['Attach_name']
        except:
            pass

        attach_format = ['.rtf', '.docx', '.pdf', '.doc']
        if 'attachname' in self.data:
            if self.data['attachname'] != None and True in list(map(self.data['attachname'].endswith, attach_format)):
                pass
            else:
                self.data.update({'attachname': None})
                self.data.update({'attach': '0'})
        else:
            self.data.update({'attachname': None})
            self.data.update({'attach': '0'})

    def check_email(self, From, Subject, msgid):
        check_list = []
        def connect_database():
            conn = pyodbc.connect('DRIVER=SQL Server;'
                                  'SERVER=hitechdblab.globalhuntindia.com;'
                                  'Database=HitechDB;'
                                  'UID=hitech_candi;'
                                  'PWD=token@123;')
            cursor = conn.cursor()
            return cursor

        spam_check = None, False
        cursor1 = connect_database()
        cursor1.execute('select * from dbo.mailarchiva')
        for mails in cursor1:
            self.check_email = mails[4].split(',')
            print(self.check_email)

        cursor2 = connect_database()
        cursor2.execute('select * from dbo.mailarchiva')
        for subjects in cursor2:
            self.check_subject = subjects[4].split(',')
            print(self.check_subject)

        cursor3 = connect_database()
        cursor3.execute('select * from dbo.mailarchivalogs1')
        for messageid in cursor3:
            self.check_messageId.append(messageid[3])
            print(self.check_messageId)

        if From in self.check_email:
            spam_check = False
        elif Subject in self.check_subject:
            spam_check = False
        elif msgid in self.check_messageId:
            spam_check = False
        else:
            spam_check = True
        if spam_check == False:
            insert_db = connect_database()
            insert_db.execute(
                "insert into mailarchivalogs1 (sendDate, [from], messageId, migrated, status) values(?,?,?,?,?)",
                (
                datetime.datetime.strptime(self.data['sentdate'], '%Y%m%d%H%M%S%f'), self.data['from'], self.data['id'],
                datetime.datetime.now(), 'NotMigrated'))
            insert_db.commit()
        return spam_check


    def elasticsearch_indexing(self):
        give = {'From': self.data['from'], 'Status': 'Migrated', 'archiveDate': self.data['archivedate']}
        self.get_fields.update(give)
        def connect_database():
            conn = pyodbc.connect('DRIVER=SQL Server;'
                                  'SERVER=hitechdblab.globalhuntindia.com;'
                                  'Database=HitechDB;'
                                  'UID=hitech_candi;'
                                  'PWD=token@123;')
            cursor = conn.cursor()
            return cursor

        def search_candidate(index_name, data_check, check_field):
            xx = self.es.search(index_name,
                                body={"query": {"term": {check_field + ".keyword": {"value": data_check}}}})
            return xx['hits']['total'], xx

        def candidate_insert(index_name, body_data):
            xx = self.es.index(index_name, body_data)
            return xx

        Others = True
        res1, value1 = search_candidate('candidate', self.data['from'], 'email')
        res2, value2 = search_candidate('contact',  self.data['from'], 'officeEmailID')

        def decode(input1):
            string = bytes(input1, 'utf-8')
            byte = BytesIO(base64.b64decode(string))
            data = parser.from_buffer(byte)
            if data.get('content'):
                return data['content']
            else:
                return None

        if res1:
            print('A candidate with this email found in Candidate collection')
            self.data['source'] = 'Candidate'
            self.data["sourceId"] = value1['hits']['hits'][0]['_id']
            if self.data['attach'] != '0':
                self.data.update({'attach': True})
            else:
                self.data.update({'attach': False})
            pprint.pprint(self.data)
            xx = candidate_insert('mail', json.dumps(self.data))
            insert_db = connect_database()
            insert_db.execute(
                "insert into mailarchivalogs1 (sendDate, [from], messageId, migrated, status) values(?,?,?,?,?)",
                (
                datetime.datetime.strptime(self.data['sentdate'], '%Y%m%d%H%M%S%f'), self.data['from'], self.data['id'],
                datetime.datetime.now(), 'Email/Candidate'))
            insert_db.commit()
            self.get_fields.update({'Type': "Candidate"})
            Others = False

        if res2:
            print('A Contact with this email adress found in contact collection')
            self.data['source'] = 'Contact'
            self.data["sourceId"] = value2['hits']['hits'][0]['_id']
            if self.data['attach'] != '0':
                self.data.update({'attach': True})
            else:
                self.data.update({'attach': False})
            xx = candidate_insert('mail', json.dumps(self.data))
            insert_db = connect_database()
            insert_db.execute(
                "insert into mailarchivalogs1 (sendDate, [from], messageId, migrated, status) values(?,?,?,?,?)",
                (
                datetime.datetime.strptime(self.data['sentdate'], '%Y%m%d%H%M%S%f'), self.data['from'], self.data['id'],
                datetime.datetime.now(), 'Email/Contact'))
            insert_db.commit()
            self.get_fields.update({'Type': "Contact"})
            Others = False

        if Others:
            email1 = self.data['from']
            email = email1.split('@')[1]
            pat = '[a-z]+\.(com|org|in|edu|hr|tr|bs|fn)$'
            domain_list = ['gmail.com', 'yahoo.com', 'yahoo.in', 'hotmail.com', 'outlook.com', "live.com",
                           'rediffmail.com',
                           'bing.com', 'hotmail.co.uk', 'aol.com', 'hotmail.fr', 'ymail.com', 'yahoo.co.in']
            check = False
            for i in range(len(domain_list)):
                if domain_list[i] in email:
                    check = True
                    break
            condition = True
            if check:
                self.data.update({"source": "Possible Candidate"})
                if self.data.get('attachments'):
                    a = None
                    data_json = {
                        "email": self.data['from'],
                        "resumeName": self.data['attachname'],
                        'resume': decode(self.data['attachments'])}

                    data1 = self.data['attachments']
                    json_data = json.dumps({"text": data1, "doc_type": "resume"})
                    url = "https://parsinglab.globalhuntindia.com/api/ResumeParser/"
                    ss = requests.post(url, data=json_data,
                                       headers={'Content-type': 'application/json', 'Accept': 'application/json'})
                    if '200' in str(ss):
                        a = json.loads(ss.text)['data']
                        if a:
                            for k, v in a.items():
                                data_json.update({k: v})
                    else:
                        pass
                    print("Candidate resume is parsed and stored in candidatebkp collection")
                    candidate_insert('candidatebkp2', json.dumps(data_json))

                    insert_db = connect_database()
                    insert_db.execute(
                        "insert into mailarchivalogs1 (sendDate, [from], messageId, migrated, status) values(?,?,?,?,?)",
                        (datetime.datetime.strptime(self.data['sentdate'], '%Y%m%d%H%M%S%f'), self.data['from'],
                         self.data['id'], datetime.datetime.now(), 'Candidatebkp'))
                    insert_db.commit()
                    self.get_fields.update({'Type': "Candidatebkp"})
                else:
                    print("A possible Candidate")
                    if self.data['attach'] != '0':
                        self.data.update({'attach': True})
                    else:
                        self.data.update({'attach': False})
                        candidate_insert('mail', json.dumps(self.data))
                        insert_db = connect_database()
                        insert_db.execute(
                            "insert into mailarchivalogs1 (sendDate, [from], messageId, migrated, status) values(?,?,?,?,?)",
                            (datetime.datetime.strptime(self.data['sentdate'], '%Y%m%d%H%M%S%f'), self.data['from'],
                             self.data['id'], datetime.datetime.now(), 'Possibel Candidate'))
                        insert_db.commit()
                        self.get_fields.update({'Type': "Possible Candidate"})
                condition = False

            elif (re.search(pat, email1)) and condition:
                print("A possible Contact")
                self.data.update({"source": "possible Contact"})
                data_f2 = self.data
                if data_f2.get('attachments'):
                    data_f2.update({'attachments': True})
                else:
                    data_f2.update({'attachments': False})

                if data_f2.get('attachname'):
                    data_f2.update({'attachName': data_f2['attachname']})
                    del data_f2['attachname']
                else:
                    data_f2.update({'attachName': None})

                if data_f2['attach'] != '0':
                    data_f2.update({'attach': True})
                else:
                    data_f2.update({'attach': False})
                    xx = candidate_insert('mail', json.dumps(data_f2))
                    insert_db = connect_database()
                    insert_db.execute(
                        "insert into mailarchivalogs1 (sendDate, [from], messageId, migrated, status) values(?,?,?,?,?)",
                        (datetime.datetime.strptime(self.data['sentdate'], '%Y%m%d%H%M%S%f'), self.data['from'],
                         self.data['id'], datetime.datetime.now(), 'EmailContact'))
                    insert_db.commit()
                    self.get_fields.update({'Type': "Possible Contact"})

            else:
                print('This email was neither found in contacts nor in candidate collections')
                self.data.update({"source": 'Others'})
                self.data.update({'from': self.data['from']})
                xx = candidate_insert('oth1', json.dumps(self.data))
                insert_db = connect_database()
                insert_db.execute(
                    "insert into mailarchivalogs1 (sendDate, [from], messageId, migrated, status) values(?,?,?,?,?)",
                    (datetime.datetime.strptime(self.data['sentdate'], '%y%m%d%H%M%S%f'), self.data['from'],
                     self.data['id'], datetime.datetime.now(), 'Others'))
                self.get_fields.update({'Type': "Others"})

    def loop_check(self, loop_range, api_response):
        get_details = []
        count = 0

        for i in range(loop_range):
            self.data = {}
            self.get_fields = {}
            self.check_subject = []
            self.check_email = []
            self.check_messageId = []

            uniqueID = api_response['searchResults'][i]['blobId']['uniqueId']
            volumeID = api_response['searchResults'][i]['blobId']['volumeId']
            MigrationWindow.modify_get_second_api_response(self, volumeID, uniqueID)
            MigrationWindow.cleaning_fields_function(self)
            condition = MigrationWindow.check_email(self, self.data['from'], self.data['subject'], self.data['id'])
            print(condition)
            if condition:
                count = count + 1
                MigrationWindow.elasticsearch_indexing(self)
            else:
                give = {'From': self.data['from'], 'Status': 'Not Migrated', 'archiveDate': self.data['archivedate'],
                        'Type': 'Excluded'}
                self.get_fields.update(give)
            a1 = str(self.get_fields['From'])
            a2 = str(self.get_fields['Status'])
            a3 = str(datetime.datetime.strptime(self.data['archivedate'], '%Y%m%d%H%M%S'))
            try:
                a4 = str(self.get_fields['Type'])
            except:
                pass
            a5 = str(datetime.datetime.strptime(self.data['sentdate'], '%Y%m%d%H%M%S'))
            a6 = str(self.data['id'])
            self.ids.total_migrated_id.text = "Migrated:  "+str(count)
            label = self.ids.products

            details = BoxLayout(size_hint_y=None, height=30,pos_hint={'top': 1})
            label.add_widget(details)
            id = Label(text=str(i), size_hint_x=0.03, color=(0.06,0.45,0.45,1), halign= 'right')
            email = Label(text=a1, size_hint_x=0.20, color=(0.06,0.45,0.45,1))
            status = Label(text=a2, size_hint_x=0.14, color=(0.06,0.45,0.45,1))
            archivedate = Label(text=a3, size_hint_x=0.15, color=(0.06,0.45,0.45,1))
            type = Label(text=a4, size_hint_x=0.15, color=(0.06,0.45,0.45,1))
            sentdate = Label(text=a5, size_hint_x=0.15, color=(0.06,0.45,0.45,1))
            messageid = Label(text=a6, size_hint_x=0.18, color=(0.06,0.45,0.45,1))

            details.add_widget(id)
            details.add_widget(email)
            details.add_widget(status)
            details.add_widget(archivedate)
            details.add_widget(type)
            details.add_widget(sentdate)
            details.add_widget(messageid)


    def get_details(self):
        start_date = self.ids.start_field.text
        end_date = self.ids.end_field.text
        range = self.ids.range_field.text
        condition = self.check_input_conditions(start_date, end_date, range)
        if condition:
            url = configfile().configure_details.get('Restclient','rest') + '?query=sentdate:['+str(start_date)+ ' TO ' +str(end_date)+ ']'
            a1 = json.loads(requests.get(url, headers={'authorization': 'Basic Uk9PVDphZG1pbjphZG1pbkAxMjM='}).text)
            loop_range = a1['totalHits']
            self.ids.total_records_id.text = "Total Records Found: "+ str(loop_range)
            self.loop_check(loop_range, a1)
        else:
            self.show_popup
    def thread(self):
        self.thrd = threading.Thread(target=self.get_details, daemon=True)
        self.thrd.start()
    def clean(self):
        self.ids.start_field.text = ''
        self.ids.end_field.text = ''
        self.ids.range_field.text = ''
        self.ids.total_records_id.text = 'Total Records Found:'
        print(self.thrd.current_thread())

    def exit(self):
        App.get_running_app().stop()

    def check_input_conditions(self, val1, val2, val3):
        if val1.isdigit and val2.isdigit() and val3.isdigit():
            if val1 < val2 and len(str(val1)) == 12 and len(str(val2)) == 12:
                return True
            else:
                return False
        else:
            return False
    @property
    def show_popup(self):
        show = P()
        popupWindow = Popup(title='Alert', content=show,auto_dismiss=True, size_hint=(None,None), size=(350,150))
        popupWindow.open()


class Get_User:
    def __init__(self):
        pass

    def get_response(self, url):
        resp_ = requests.get(url)
        resp_json = json.loads(resp_.text)
        user_list = []
        for i in range(len(resp_json)):
            if resp_json[i]['emailid'] != '':
                user_list.append(resp_json[i]['emailid'])
        return user_list

class MigrationApp(App):
    def build(self):
        main_window = Email_Screen()
        #importedList = Get_User().get_response('http://stagingapi.globalhuntindia.com/MultiPlateformAPI/api/InternalSearch/GetUserlist')

        # for name in importedList:
            # NameLabel = ButtonLabel(text=(name))

            # main_window.ids.selected_list.ids.content.add_widget(NameLabel)
        return Display()

if __name__ == '__main__':
    MigrationApp().run()




