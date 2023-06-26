import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
import json
import os
from time import sleep

class Bot:
    @staticmethod
    def save_json(dir_name:str, json_obj:dict, json_name:str):
        '''make directory and save 'json_name:str' in that 'dir_name:str'
        '''
        try:
            os.mkdir(os.path.join(os.getcwd(), dir_name))
        except:
            print(f'Directory ---{dir_name}--- already exists')
        path = os.path.join(os.getcwd(), 'l')
        with open(f'{dir_name}/{json_name}.json', 'w', encoding='utf-8') as file:
            json.dump(json_obj, file, indent=4, sort_keys=True, ensure_ascii=False)

    
    def set_session(self,url:str, proxies:dict=None, agent:str=None)->str:
        '''take url with ivent, proxies, user-agent
        'https://spb.ticketland.ru/teatry/bdt-imtovstonogova/privideniya-bdt-imeni-tovstonogova/'
        end url with '/' IMPOTRANT!

        set Session, set user-agent, set tl_csrf token, set ivent_name
         
        return url with_seats
        https://spb.ticketland.ru/teatry/bdt-imtovstonogova/privideniya-bdt-imeni-tovstonogova/20230625_1800-4595645/ '''

        self.session = requests.Session()
        agent = UserAgent().random
        #proxies = {'http': '127.0.0.1:8080',  #for del in product
                #'https': '127.0.0.1:8080'}
        headers = {'user-agent': agent}  # for delete in product
        self.session.headers.update(headers)
        #self.session.proxies.update(proxies)

        print('Try to connect', url)
        try:
            r = self.session.get(url, verify=False)
            print(r.status_code)
        except:
            raise Exception(f'Cannot connect {url}')
        else:
            if r.ok:
                print(f'Successfull conect {url}')
            else:
                raise Exception(f'{r.status_code}Cannot connect {url}')
        self.cookies = {key:value for key, value in r.cookies.items()}


        one_soup = BeautifulSoup(r.text, 'lxml')
        try:
            self.tl_csrf = one_soup.find('meta', {'name': "csrf-token"}).get('content')
        except AttributeError as er:
            raise Exception('Cannot find tl_csrf TOKEN')
        
        self.main_url = 'https://spb.ticketland.ru'
        self.ivent_name = url.split('/')[-2] # example : privideniya-bdt-imeni-tovstonogova
        button_link_buy_tiket = one_soup.find('a', {'href': re.compile(fr'{self.ivent_name}')}).get('href')
        button_link_buy_tiket = self.main_url + button_link_buy_tiket # URL WITH SCHEME SEATS
        sleep(3)
        return button_link_buy_tiket
    
    def get_json_with_all_availible_places(self, url:str, write_json:bool=False)->dict:
        '''Requests TO URL WITH SHEME SEATS ...privideniya-bdt-imeni-tovstonogova/20230625_1800-4595645/
            
        find webPageId

        XMLHttpRequest to ->
        'https://spb.ticketland.ru/hallview/map/{webPageId}/?json=1&all=1&isSpecialSale=0&tl-csrf={CSRF}'
        
        return response.json():dict with all free places 

        if write_json == True -> write json
        '''
        print('Try to connect', url)
        r = self.session.get(url = url)
        two_soup = BeautifulSoup(r.text, 'lxml')
        try:
            text = two_soup.find('script', string=lambda s: 'webPageId' in s).text # find  webPageId
            self.webpageid = re.search(r'webPageId: \d+', text)[0].split()[-1]
        except:
            raise Exception('Cannot find webPageId')
        
        
        XMLHttpRequest = 'https://spb.ticketland.ru/hallview/map/' + self.webpageid + '/'
        print('requests XMLHttpRequest to', XMLHttpRequest)
        params = {'json':1,
                'all':1,
                'isSpecialSale':0,
                'tl-csrf':self.tl_csrf}
        headers = {'X-Requested-With':'XMLHttpRequest'}
        r1 = self.session.get(url=XMLHttpRequest, headers=headers,params=params) # get all seets
        if r1.ok:
            if write_json:
                self.save_json(self.ivent_name+str(self.webpageid), r1.json(),self.ivent_name)
            return r1.json()
        else:
            raise Exception('XMLHttpRequest cannot get json with all seats')

    
    def json_data_override(self,json_data:dict, write_json:bool=False)->dict:
        '''takes the resulting json wich we recived from 
        'https://spb.ticketland.ru/hallview/map/{webPageId}/?json=1&all=1&isSpecialSale=0&tl-csrf={CSRF}'
        and convert it to convenient format

        {'Места за креслами, левая сторона':{'4': {'82': {'cypher':'YOdOOe...', 'price':1000,  'tariff': 406819}}}}
        {'name_of_place':{'row':{'place':{'cypher':'str', 'price':int ,'tariff':'int'}}
        
        you can save if install write_json==True
        '''
        availible_seats = json_data
        try:
            section_names = {i.get('section')['name']:{} for i in availible_seats['places']}
            for section in section_names:
                for j in availible_seats['places']:
                    if section == j['section']['name']:
                        section_names.setdefault(section,{j['row']:{}}).update({j['row']:{}})
            for j in availible_seats['places']:
                section_names[j['section']['name']][j['row']].setdefault(j['place'],{'price':j['price'],'tariff':j['tariff'],'cypher':j['cypher']})
            self.section_names = section_names
        except:
            raise Exception('Mistake with json override. See "Bot.json_data_override()"')
        else:
            if write_json:
                self.save_json(self.ivent_name+str(self.webpageid), section_names, 'NEW' + self.ivent_name )
        
        return self.section_names
    
    def show_places(self, json_data:dict)->dict:
        '''for easy viewing of availible seats
        '''
        pass

    def buy_function(self, seats:str, row:int, places_count:int, \
                     name:str, surname:str, email:str, json_data:dict=None)->str:
        '''Seats -> "Балкон 3-го яруса левая сторона",
        row -> 1,
        places_count -> min(1)-max(8) 'how many tickets to buy (take in order form from json)'
        name -> 'Ivan', surname -> 'Ivanov', email:'ivan@gmail.com'

        json_data -> you can load you own scheme,
        if  json_data is None -> it used self.section_names
        '''
        if not json_data:
            json_data = self.section_names
        # print(json_data[seats][str(row)])
        # print(json_data['Балкон 3-го яруса левая сторона'])
        box_with_tickets = [ i for i in json_data[seats][str(row)] ]
        try:
            box_with_tickets = sorted([ i for i in json_data[seats][str(row)]], key=int)
        except:
            raise Exception("Check the correct seats or row")
        
        select_place = 'https://spb.ticketland.ru/hallPlace/select/'
        headers = {'X-Requested-With':'XMLHttpRequest'}
        for i in box_with_tickets[:places_count]:
            data = {'cypher': json_data[seats][str(row)][str(i)]['cypher'],
                    'tax':json_data[seats][str(row)][str(i)]['tariff'],
                    'tl-csrf':self.tl_csrf}
            try:
                select = self.session.post(url=select_place,headers=headers,data=data) #change place we want
            except:
                print(f'Cannot buy {seats} row {row} place {i}')
            else:
                try:
                    print('ticketCount', select.json()['ticketCount'])
                    print('basketPrice', select.json()['basketPrice'])
                except:
                    print('incorrect json')
        print('Ok, we select places, now generate url for pay...')

        data = {'email': email,
        'name': name,
        'surname': surname,
        'payment': 'card'}
        url_for_pay = 'https://spb.ticketland.ru/order/createAnonymousOrder/'
        try:
           create_order = self.session.post(url=url_for_pay, headers=headers, data=data) # createAnonymousOrder
        except:
            raise Exception('cannot createAnonymousOrder')
        # print(create_order)
        # print(create_order.json())
        else:
            try:
                print('errors', create_order.json()['error'])
            except:
                raise Exception('SOME ERRORS with createAnonymousOrder')
        
        try:
            payment_url = self.main_url + create_order.json()['url']
            data = {'sessOrderId': create_order.json()['orderId'],
                    'paymentWay': create_order.json()['params']['paymentWay']}
        except:
            raise Exception('Problem with createAnonymousOrder.json()')
        
        try:
            payment = self.session.post(url=payment_url,headers=headers,data=data) # some payment work
        except:
            raise Exception('cannot create payment')
        
        try:
            page_for_pay = payment.json()['url'] + '?mdOrder=' + payment.json()['get']['mdOrder']
        except:
            raise Exception('Cannot create "page_for_pay"')
        
        return page_for_pay

#url = 'https://spb.ticketland.ru/teatry/bdt-imtovstonogova/privideniya-bdt-imeni-tovstonogova/'
url = 'https://spb.ticketland.ru/teatry/bdt-imtovstonogova/dzhuletta/'
x = Bot() 

#new_url = x.set_session(url) # set Session
#t = x.get_json_with_all_availible_places(new_url)
#x.json_data_override(t, write_json=True) # SEE JSON ON YOUR PC TO SELECT seats AND row 

#next  fill -> seats='str',row=int, places_count=int, name='str',
#                    surname='str', email='str', json_data=box

def run(url):
    ''' rung after filling
    '''
    x.set_session(url)
    with open('NEWdzhuletta.json', 'r', encoding='utf-8') as file:
        box = json.load(file)
        link_for_pay = x.buy_function(seats='Балкон 3-го яруса левая сторона',
                    row=4, places_count=8, name='petr1',
                    surname='valera2', email='mail2@gmail.com', json_data=box)
        
        print(link_for_pay)

run(url)



