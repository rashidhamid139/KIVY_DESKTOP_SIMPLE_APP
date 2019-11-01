from kivy.app import App 

from kivy.lang import Builder 

from kivy.uix.widget import Widget 

from kivy.uix.label import Label 

from kivy.uix.screenmanager import ScreenManager, Screen 

from kivy.uix.boxlayout import BoxLayout 

from kivy.properties import ObjectProperty 

from kivy.uix.tabbedpanel import TabbedPanel 

#from kivy.adapter.listadapter import ListAdapter 

#from kivy.uix.listview import ListItemButton 

from kivy.uix.floatlayout import FloatLayout 

from kivy.uix.popup import Popup 

import os 

import configparser 

  

  

class Config_Writer(object): 

    def config_write_func(self): 

        return configparser.ConfigParser() 

  

  

  

class P(FloatLayout): 

    pass 

  

class Display(BoxLayout): 

    pass 

     

class Screen_Two(Screen): 

    def display(self): 

        print("Hello") 

     

class Screen_One(Screen): 

    def get_details(self): 

        start_date = self.ids.start_field.text 

        end_date = self.ids.end_field.text 

        range = self.ids.range_field.text 

        condition = self.check_input_conditions(start_date, end_date, range) 

        if condition: 

            print("Y") 

            pass 

        else: 

            print("N") 

            self.show_popup 

         

    def clean(self): 

        self.ids.start_field.text='' 

        self.ids.end_field.text = '' 

        self.ids.range_field.text = '' 

    def Exit(self): 

        App.get_running_app().stop() 

  

  

    def check_input_conditions(self,val1, val2, val3): 

        if val1.isdigit and val2.isdigit() and val3.isdigit(): 

            if val1<val2 and len(str(val1))==12 and len(str(val2))==12: 

                return True 

            else: 

                return False 

        else: 

            return False         

    @property  

    def show_popup(self): 

        show = P() 

        popupWindow = Popup(title='Error', content=show, size_hint=(None,None), 

                             size=(350,150)) 

        popupWindow.open() 

         

class Screen_Third(Screen): 

    def add(self): 

        email = self.ids['exclude_email_id'].text 

        if email: 

            view = email+ ',\n'+ self.ids['exclude_email_view'].text 

            self.ids['exclude_email_view'].text= view 

        else: 

            pass 

    def clear(self): 

        self.ids['exclude_email_view'].text ='' 

        self.ids['exclude_email_id'].text='' 

    def save(self): 

        os.chdir(os.environ['USERPROFILE']+ '\desktop') 

        config= Config_Writer().config_write_func() 

        config['Exclude_Email']={'emails': self.ids['exclude_email_view'].text} 

        with open('example.ini', 'a') as configfile: 

            config.write(configfile) 

         

  

class Screen_Fourth(Screen): 

    def add(self): 

        email = self.ids['exclude_subject_id'].text 

        if email!='': 

            view = email+ '\n'+ self.ids['exclude_subject_view'].text 

            self.ids['exclude_subject_view'].text= view 

        else: 

            pass 

    def clear(self): 

        self.ids['exclude_subject_view'].text ='' 

        self.ids['exclude_subject_id'].text='' 

    def save(self): 

        os.chdir(os.environ['USERPROFILE']+ '\desktop') 

        config= Config_Writer().config_write_func() 

        config['Exclude_Subject']={'Subjects': self.ids['exclude_subject_view'].text} 

        with open('example.ini', 'a') as configfile: 

            config.write(configfile) 

     

class Screen_Fifth(Screen): 

    def save(self): 

        os.chdir(os.environ['USERPROFILE']+ '\desktop') 

        config= Config_Writer().config_write_func() 

        config['Database_conn']={'conn': self.ids['connection_id'].text, 

                                'Server': self.ids['server_id'].text, 

                                'Database': self.ids['database_id'].text, 

                                'UID': self.ids['user_id'].text, 

                                'PWD': self.ids['password_id'].text} 

        with open('example.ini', 'a') as configfile: 

            config.write(configfile) 

  

class Screen_Six(Screen): 

    def save(self): 

        os.chdir(os.environ['USERPROFILE']+ '\desktop') 

        config= Config_Writer().config_write_func() 

        config['Elasticsearch']={'endpoint': self.ids['endpoint_id'].text, 

                                'candidate_collection': self.ids['candidate_collection_id'].text, 

                                'mail_collection': self.ids['contact_collection_id'].text} 

        with open('example.ini', 'a') as configfile: 

            config.write(configfile)     

class Screen_Seven(Screen): 

    def save(self): 

        os.chdir(os.environ['USERPROFILE']+ '\desktop') 

        config= Config_Writer().config_write_func() 

        config['collections']={'cand': self.ids['candidate_store_id'].text, 

                                'cont': self.ids['contact_store_id'].text} 

        with open('example.ini', 'a') as configfile: 

            config.write(configfile) 

     

class Screen_Eight(Screen): 

    def save(self): 

        os.chdir(os.environ['USERPROFILE']+ '\desktop') 

        config= Config_Writer().config_write_func() 

        config['Resume_Parsing_Api']={'url': self.ids['resume_parsing_id'].text} 

        with open('example.ini', 'a') as configfile: 

            config.write(configfile) 

     

class DemoApp(App): 

    def build(self): 

        return Display() 

         

if __name__ =='__main__': 

    DemoApp().run() 