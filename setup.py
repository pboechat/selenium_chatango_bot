#!/usr/bin/env python

from setuptools import setup

setup(name='selenium-chatango-bot',
      packages=['selenium_chatango_bot'],
      package_data={'': ['bot_msgs.txt', 'bot_config.json', 'page_config.json']},
      version='1.0.0',
      install_requires=['selenium>=3.13.0'],
      description='Selenium Chatango Bot',
      author='Pedro Boechat',
      author_email='pboechat@gmail.com',
      entry_points={'console_scripts': ['selenium_chatango_bot = selenium_chatango_bot.selenium_chatango_bot:main']})
