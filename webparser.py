import requests as rq
from bs4 import BeautifulSoup as BS

def get_data()->list:

    data = []
    url = "https://mai.ru/education/schedule/detail.php?group=%D0%9C4%D0%9E-112%D0%91-21"
    html = rq.get(url).text
    soup = BS(html, "html.parser")
    schedule_content = soup.find(id="schedule-content")
    for day in schedule_content.find_all(class_="sc-container"):
        day_data = []
        week_day = day.find(class_="sc-table-col").text[-2:]
        date = day.find(class_="sc-table-col").text[:-2]
        day_data += [{"date" : date, "week_day" : week_day}]
        for item in day.find("div", class_="sc-table sc-table-detail").find_all("div", class_="sc-table-row"):
            time = item.find(class_="sc-item-time").text.strip()
            lesson_type = item.find(class_="sc-item-type").text.strip()
            lesson = item.find(class_="sc-title").text.strip()
            tutor = " | ".join([name.text.strip() for name in item.find("div", class_="sc-item-title-body").find_all("span", class_="sc-lecturer")])
            location = item.find_all(class_="sc-table-col sc-item-location")[1].text.strip()
            day_data += [{"lesson" : lesson, "tutor" : tutor, "time" : time, "type" : lesson_type, "location" : location}]
        data += [day_data]
    return data
