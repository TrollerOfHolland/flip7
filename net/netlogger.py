import datetime


class Logger:

    def log(self, content, printContent=True):
        timestamp = datetime.datetime.now()
        formatted_time = timestamp.strftime('%b %d %Y %H:%M:%S') + ':'

        try:
            content = str(content)
        except:
            print('LOGGER: UNKNOWN TYPE')
            return

        if(printContent):
            print(formatted_time)
            print(content)

        with open(self._logfile, 'a') as file_handle:
            file_handle.write(formatted_time + '\n')
            file_handle.write(content)

    def __init__(self, message=''):
        self._logfile = 'netlog.log'
        if(message):
            self.log(message, printContent=False)
        else:
            self.log('Started Logger', printContent=False)
