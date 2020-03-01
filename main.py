import time
import json
import requests
import datetime
from datetime import datetime as dt
import random
import logging
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

def set_log(log_level):
    """Set logger
    Args:
        int: Log level
    Returns:
        obj: logger obj
    """
    logging.basicConfig(level=log_level)
    logger = logging.getLogger('Log')    

    # print for console
    sh = logging.StreamHandler()
    logger.addHandler(sh)
    
    # print for log file
    fh = logging.FileHandler('test.log')
    logger.addHandler(fh)
    return logger

logger = set_log(logging.INFO)

# configuration settings
f = open('./config_setting.json', 'r')
CONFIG = json.load(f)
dt_now = dt.now()

# browser setting
browser = webdriver.Chrome()

# start / end date
start = {
    'datetime' : dt.strptime(CONFIG['date']['from'], CONFIG['date']['format']),
    'str': {
        'date'     : CONFIG['date']['from'],
        'year'     : dt.strptime(CONFIG['date']['from'], CONFIG['date']['format']).strftime('%Y'),
        'month'    : dt.strptime(CONFIG['date']['from'], CONFIG['date']['format']).strftime('%m'),
        'day'      : dt.strptime(CONFIG['date']['from'], CONFIG['date']['format']).strftime('%d')
    }
}
end = {
    'datetime' : dt.strptime(CONFIG['date']['to'], CONFIG['date']['format']),
    'str': {
        'date'     : CONFIG['date']['to'],
        'year'     : dt.strptime(CONFIG['date']['to'], CONFIG['date']['format']).strftime('%Y'),
        'month'    : dt.strptime(CONFIG['date']['to'], CONFIG['date']['format']).strftime('%m'),
        'day'      : dt.strptime(CONFIG['date']['to'], CONFIG['date']['format']).strftime('%d')
    }
}

def login(user, password):
    """Login to pepup system
    login from selenium
    Args:
        user (str): user name
        password (str): password
    """
    logger.info(u'Attempt tp log in : user = ' + str(user) + ', pass = XXXXXXXX')
    browser.get(CONFIG['url']['login'])
    browser.find_element_by_css_selector('#sender-email').send_keys(user)
    browser.find_element_by_css_selector('#user-pass').send_keys(password)
    browser.find_element_by_name('commit').click()
    logger.info(u'Success log in : user = ' + str(user) + ', pass = XXXXXXXX')

def get_session_id():
    """Obtain session id
    Returns:
        str: session id
    """
    cookies = browser.get_cookies()
    return [ item['value'] for item in cookies if item['domain'] == 'pepup.life' ][0]

def regist_by_api(regist_date, end_date, session_id):
    """Regist walking steps and sleep time
    Args:
        session_id (str): session id 
    """
    logger.info(u'Regis via api for : ' + str(session_id))
    url = CONFIG['url']['api']
    session = requests.session()
    headers = get_headers_for_api(session_id)
    # roop from start date to end date
    err_cnt = 0
    # continue untill regit date is over end date or error count is over 5
    while regist_date <= end_date and err_cnt < CONFIG['error']['limit']:
        logger.info(u'run regist date : ' + str(regist_date))
        step_data = create_data_step(regist_date.strftime(CONFIG['date']['format']))
        sleep_data = create_data_sleep(regist_date.strftime(CONFIG['date']['format']))
        # regist data
        time.sleep(0.1)
        res_step = session.post(url, json=step_data, headers=headers)
        time.sleep(0.1)
        res_sleep = session.post(url, json=sleep_data, headers=headers)
        if has_error(res_step.status_code):
            logger.error(u'Failed to regist step data: status = ' + str(res_step.status_code) + ': message = ' + str(res_step.text))
            err_cnt += 1
        if has_error(res_sleep.status_code):
            logger.error(u'Failed to regist step data: status = ' + str(res_sleep.status_code) + ': message = ' + str(res_sleep.text))
            err_cnt += 1
        logger.info(u'step: ' + str(step_data))
        logger.info(u'sleep: ' + str(sleep_data))
        # Update regist date
        regist_date += datetime.timedelta(days=1)
    else:
        logger.info(u'Regist from ' + str(start["datetime"]) + ' to ' + str(end["datetime"]))
        logger.info(u'INFO: Error count =' + str(err_cnt))

def get_headers_for_api(session_id):
    return {
        'method'     : 'POST',
        'content-type': 'application/json; charset=UTF-8',
        'cookie'     : 'pepup_sess=' + str(session_id)
    }

def template_post_data(value_type: str, value: int, timestamp :str):
    """Create template post data
    Args:
        value_type (str): 'step_count' or 'sleeping'
        value (int): regist value
        timestamp (str): Date string with YYYY-MM-DD format
    Return:
        obj: Request body data for regist
    """
    return {
        'values': [
            {
                'source'    : 'web',
                'source_uid': 'web',
                'timestamp' : str(timestamp),
                'value'     : str(value),
                'value_type': str(value_type)
            }
        ],
        'datatime': end["str"]["date"] + 'T00:00:00.000Z'
    }

def create_data_sleep(date: str):
    value = CONFIG['sleep']['time'] * 60
    return template_post_data('sleeping', value, date)

def create_data_step(date: str):
    """Request body data for step count
    Args:
        date (str): Date string with YYYY-MM-DD format
    Returns:
        obj: Request body data for step count
    """
    value = random.randint(CONFIG['step']['from'], CONFIG['step']['to'])
    return template_post_data('step_count', value, date)

def has_error(status: int):
    """Evaluate if response has error
    Returns:
        status (bool): http status is not success than true
    """
    return status < 200 or status > 299

def regist_by_selenium(regist_date, end_date):
    """Regist actions:
    regist actions from selenium
    Args:
        regist_date (datetime): Datetime object for regist date
        end_date (datetime)   : Datetime object for end date
    """
    btn_date = ''
    card_selector = '.afxg5u-0'
    card_title_selector = '.afxg5u-1'
    regist_btn_selector = '.sc-1ccba62-8 button'
    cards_cnt = 0
    while regist_date <= end_date:
        year = regist_date.strftime('%Y')
        month = regist_date.strftime('%m')
        browser.get(CONFIG['url']['regist'] + '/' + year + '/' + month.lstrip('0'))
        for card in browser.find_elements_by_css_selector(card_selector):
            cards_cnt += 1
            if cards_cnt <= 2 : # the card 1 and 2 is registed from regist_by_api
                continue
            item_name = card.find_element_by_css_selector(card_title_selector).text
            logger.info(u'Regist for ' + item_name)
            for btn in card.find_elements_by_css_selector(regist_btn_selector):
                if not btn.text:
                    continue
                logger.info(u'Regist on ' + regist_date.strftime('%Y/%m') + '/' + btn.text)
                btn_date = dt(regist_date.year, regist_date.month, int(btn.text)) 
                if btn_date < regist_date:
                    logger.info('Skipping...')
                    continue
                elif btn_date > end_date:
                    logger.info('Breaking...')
                    break
                # logger.info(u'Run...')
                btn.click()
                click_modal()
        else:
            cards_cnt = 0 # initialize
            regist_date = btn_date + datetime.timedelta(days=1)
            logger.info('Update regist date on ' + str(regist_date))

def click_modal():
    modal_selector = '.ycydyz-0'
    labels_selector = '.ycydyz-0 label'
    close_selector = '.ycydyz-0 button'
    modal = browser.find_element_by_css_selector(modal_selector)
    logger.info(u'Click...')
    for label in modal.find_elements_by_css_selector(labels_selector):
        logger.info(u'Check for ' + label.text)
        if not label.find_element_by_css_selector('input').is_selected():
            label.find_element_by_css_selector('input').click()
    else:
        modal.find_element_by_css_selector(close_selector).click()

def main():
    """Main method"""
    logger.info("Start pepup automation script...")
    login(CONFIG['login']['user'], CONFIG['login']['password'])
    session_id = get_session_id()
    start_date = start["datetime"]
    end_date = end["datetime"]
    regist_by_api(start_date, end_date, session_id)
    regist_by_selenium(start_date, end_date)
    time.sleep(3)
    browser.close()
    logger.info('Successfully Ended from ' + start["str"]["date"] + ' to ' + end["str"]["date"])
    logger.info('Please check the following URL: ' + CONFIG["url"]["login"])

# run main script
main()