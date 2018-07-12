import json
import random
import time
import zipfile
from argparse import ArgumentParser

from pkg_resources import resource_filename
from selenium import webdriver
from selenium.webdriver.common import keys

EMOTICONS = ['*lol*', '_shhh']


def random_wait(min, max):
    if min < 0 or max < 0:
        raise Exception('min and max must be greater or equal 0')

    if min > max:
        raise Exception('min must be greater or equal than max')

    if min == max:
        return

    wait = min + int(round(random.random() * (max - min)))
    print('waiting for {} second(s)...'.format(wait))
    time.sleep(wait)


def remove_emoticons(msg):
    for emoticon in EMOTICONS:
        msg = msg.replace(emoticon, '')
    return msg


class GetOutOfLoop(Exception):
    pass


# https://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    import os

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def download(url, path, attempts=5):
    import urllib
    while attempts:
        try:
            response = urllib.request.urlopen(url, timeout=5)
            content = response.read()
            with open(path, 'wb') as file:
                file.write(content)
            break
        except urllib.URLError:
            attempts -= 1


def main():
    parser = ArgumentParser()
    parser.add_argument('--page_config', '--pc', type=str, required=False,
                        default=resource_filename(__name__, 'page_config.json'))
    parser.add_argument('--bot_config', '--bc', type=str, required=False, default=resource_filename(__name__, 'bot_config.json'))
    parser.add_argument('--bot_msgs', '--bm', type=str, required=False, default=resource_filename(__name__, 'bot_msgs.txt'))
    args = parser.parse_args()

    print("loading page config ('{}')...".format(args.page_config))
    with open(args.page_config) as file:
        page_config = json.load(file)

    if not which('chromedriver.exe'):
        download('https://chromedriver.storage.googleapis.com/2.40/chromedriver_win32.zip', 'chromedriver_win32.zip')
        with zipfile.ZipFile('chromedriver_win32.zip', 'r') as file:
            file.extractall('.')

    driver = webdriver.Chrome()
    driver.get(page_config['BASE_URL'])
    driver.maximize_window()

    driver.switch_to.frame(driver.find_element_by_xpath(page_config['IFRAME_XPATH']))

    input_field = driver.find_element_by_xpath(page_config['INPUT_FIELD_XPATH'])

    first_time = True
    while True:
        print("loading bot config ('{}')...".format(args.bot_config))
        with open(args.bot_config) as file:
            bot_config = json.load(file)

        print("loading bot bot_msgs ('{}')...".format(args.bot_msgs))
        with open(args.bot_msgs, 'r', encoding='utf-8') as file:
            bot_msgs = [line.strip() for line in file.readlines()]
        random.shuffle(bot_msgs)

        msg_seq_size = min(len(bot_msgs), bot_config['MESSAGE_SEQUENCE_SIZE'])

        sent_bot_msgs = []
        for i in range(1, msg_seq_size + 1):
            msg = bot_msgs.pop()
            print("+ [{}/{}] sending message: '{}'".format(i, msg_seq_size, msg))

            input_field.clear()
            input_field.send_keys(msg + keys.Keys.ENTER)
            sent_bot_msgs.append(remove_emoticons(msg).strip())

            if first_time:
                print("since it's the first message send, let's wait for {} second(s)...".format(
                    bot_config['FIRST_MESSAGE_SEND_WAIT']))
                time.sleep(bot_config['FIRST_MESSAGE_SEND_WAIT'])
                first_time = False

            random_wait(bot_config['MIN_MESSAGE_SEND_WAIT'], bot_config['MAX_MESSAGE_SEND_WAIT'])

        num_my_msgs = len(sent_bot_msgs)
        try:
            while True:
                print('searching the last {} message(s)...'.format(num_my_msgs))
                other_msg_els = driver.find_elements_by_xpath(page_config['MSGS_DIV_XPATH'])
                if len(other_msg_els) < num_my_msgs:
                    print('unexpected situation! len(other_msg_els) < num_my_msgs')
                    break
                for j, i in enumerate(range(num_my_msgs, 0, -1)):
                    other_msg_el = other_msg_els[-i]
                    other_msg = remove_emoticons(other_msg_el.text.strip())
                    colon_pos = other_msg.find(':')
                    if colon_pos == -1:
                        print('- [{}/{}] error parsing message, ignoring...\n(\n\tother_msg: {}\n)'.format(
                            j + 1,
                            num_my_msgs,
                            other_msg))
                        continue
                    other_msg = other_msg[colon_pos + 1:].strip()
                    my_msg = sent_bot_msgs[-i]
                    if my_msg != other_msg:
                        print("- [{}/{}] new message found, stopping...\n(\n\tmy_msg: '{}',\n\tother_msg: {}\n)".format(
                            j + 1,
                            num_my_msgs,
                            my_msg,
                            other_msg))
                        raise GetOutOfLoop
                    else:
                        print(
                            "- [{}/{}] no new message found, continuing...\n(\n\tmy_msg: '{}',\n\tother_msg: {}\n)".format(
                                j + 1,
                                num_my_msgs,
                                sent_bot_msgs,
                                other_msg))
                random_wait(bot_config['MIN_MESSAGE_POOL_WAIT'], bot_config['MAX_MESSAGE_POOL_WAIT'])
        except GetOutOfLoop:
            pass


if __name__ == '__main__':
    main()
