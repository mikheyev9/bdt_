bot1 = Bot()

1) Создать сессию , можно добавить прокси и юзер агент

url = 'https://spb.ticketland.ru/teatry/bdt-imtovstonogova/privideniya-bdt-imeni-tovstonogova/'
new_url = bot1.set_session(url) #  -> В ответ придёт url с местами для этого мероприятия

2) places = bot1.get_json_with_all_availible_places(new_url)  возвращает json со всеми доступными для покупки местами
3) bot1.json_data_override(places) - сохраняем json отсортированный по всем доступным для покупки секторам->рядам->местам в self.section_names
4) link_for_pay = bot1.buy_function(seats='Балкон 3-го яруса левая сторона',
                    row=4, places_count=8, name='petr1',
                    surname='valera2', email='mail2@gmail.com', json_data=self.section_names) возвращает ссылку для оплаты

места берутся по отсортированному порядку, исходя из полученнго jsona с доступными местами, хотел реализовать возможность покупки определенных мест,
чтобы не было покупки одних и тех же билетов




