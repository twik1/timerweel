import threading
import datetime


def executer(param):
    """
    Testcode
    :param param: Used in printout
    :return: NA
    """
    print("called at {} with {}".format(datetime.datetime.now(), param))


class Tlock:
    """
    A class of a lock for the timeweel to wait on.
    Always wait for the earliest timer or infinite if no timer in weel
    """
    def __init__(self):
        self.timeout_flag = threading.Event()
        self.mode = 1  # infinite lock

    def setmode(self, mode):
        """
        Switch between lock infinite or timeout
        :param mode: 1 = infinite, 2 = timeout
        :return: NA
        """
        if mode == 'lock':
            self.mode = 1
        else:
            self.mode = 2

    def set(self):
        """
        Switch between lockmodes
        :return: NA
        """
        self.timeout_flag.set()

    def wait(self, timeout):
        """
        The lock funtion for the timer weel
        :param timeout: a timeout in seconds to be used in mode 2
        :return:
        """
        if self.mode == 1:
            retvalue = self.timeout_flag.wait()
        else:
            retvalue = self.timeout_flag.wait(timeout)
        self.timeout_flag.clear()
        return retvalue


class Timerweel:
    """
    A timer class which sleeps untill the timer fires.
    Compleatly without polling.
    """
    def __init__(self):
        self.timerlist = []
        self.closest_timeritem = 0
        self.closest_timerindex = 0
        self.lock = Tlock()
        self.wthread = threading.Thread(target=self.worker, args=("tst",))
        # self.wflag = threading.Event()
        self.wthread.start()

    def worker(self, est):
        """
        The worker thread, only withing to do work!
        and reschedule work if timer is reccuring
        :param est: Not used
        :return: NA
        """
        while True:
            if self.lock.wait(self.closest_timeritem):
                continue

            self.timerlist[self.closest_timerindex]['run'](self.timerlist[self.closest_timerindex]['param'])
            newtimer = self.timerlist[self.closest_timerindex]['timer']
            run = self.timerlist[self.closest_timerindex]['run']
            name = self.timerlist[self.closest_timerindex]['name']
            param = self.timerlist[self.closest_timerindex]['param']
            reccure = self.timerlist[self.closest_timerindex]['reccure']
            if self.timerlist[self.closest_timerindex]['reccure'] == 'day':
                del self.timerlist[self.closest_timerindex]
                newtimer = newtimer + datetime.timedelta(days=1)
                self.add_timer(newtimer, run, name, reccure, param)
            elif self.timerlist[self.closest_timerindex]['reccure'] == 'week':
                del self.timerlist[self.closest_timerindex]
                newtimer = newtimer + datetime.timedelta(weeks=1)
                self.add_timer(newtimer, run, name, reccure, param)
            else:
                del self.timerlist[self.closest_timerindex]
                self.update_delta()

    def update_delta(self):
        """
        Function to search for the timer closest in time and update
        the workerthreads lock to fire at the correct time.
        Should be run at every change in the timer list.
        :return: NA
        """
        index = 0
        self.closest_timeritem = 0
        for item in self.timerlist:
            item['delta'] = (item['timer'] - datetime.datetime.now()).total_seconds()
            if not self.closest_timeritem or item['delta'] < self.closest_timeritem:
                self.closest_timeritem = item['delta']
                self.closest_timerindex = index
            index += 1
        if len(self.timerlist) > 0:
            self.lock.setmode('timeout')
        else:
            self.lock.setmode('lock')
        self.lock.set()

    def add_timer(self, newtimer, run, name, reccure, param):
        """
        Add a timer to timerweel
        :param newtimer: timer object, needs to be in the future
        :param run: pointer to a function that will be run at timer expire
        :param name: name of the timer entry
        :param reccure: 'once', 'day', 'week' if and how often to run the timer
        :param param: parameters sent along to the function
        :return: None
        """
        # Protect
        # current = datetime.datetime.now()
        if (newtimer - datetime.datetime.now()).total_seconds() < 0:
            # print("Timer in the past")
            return
        timeritem = {'timer': newtimer, 'run': run, 'seq': 0, 'delta': 0, 'name': name, 'reccure': reccure,
                     'param': param}
        self.timerlist.append(timeritem)
        print("Adding {} at {}, {} in list".format(name, newtimer, len(self.timerlist)))
        self.update_delta()
        # Unprotect

    def add_once_timer(self, tdatetime, run, name, param):
        """
        A function to add a timer to run one at a specific time
        :param tdatetime: string of time e.g "2020-07-12 22:02:02"
        :param run: pointer to a function that will be run at timer expire
        :param name: name of the timer entry
        :param param: parameters sent along to the function
        :return: 1 if fail, 0 if success
        """
        # Protect
        newtimer = datetime.datetime.strptime(tdatetime, "%Y-%m-%d %H:%M:%S")
        if (newtimer - datetime.datetime.now()).total_seconds() < 0:
            print("Timer in the past, not set")
            return 1
        reccure = 'once'
        self.add_timer(newtimer, run, name, reccure, param)
        return 0

    def add_every_day(self, dtime, run, name, param):
        """
        A function to add a timer to run every day at the same time
        :param dtime: string of time e.g "22:02:02"
        :param run: pointer to a function that will be run at timer expire
        :param name: name of the timer entry
        :param param: parameters sent along to the function
        :return: None
        """
        # time 22:02
        # Protect
        current = datetime.datetime.now()
        newtimer = datetime.datetime.strptime(
            "{}-{}-{} {}".format(str(current.year), str(current.month), str(current.day), dtime), "%Y-%m-%d %H:%M:%S")
        if (newtimer - datetime.datetime.now()).total_seconds() < 0:
            newtimer = newtimer + datetime.timedelta(days=1)
        reccure = 'day'
        self.add_timer(newtimer, run, name, reccure, param)
        # Unproect

    def add_every_week(self, dday, dtime, run, name, param):
        """
        A function to add a timer to run every week at the same day and time
        :param dday: "mon", "tue", "wed", "thu", "fri", "sat", "sun"
        :param dtime: string of time e.g "22:02:02"
        :param run: pointer to a function that will be run at timer expire
        :param name: name of the timer entry
        :param param: parameters sent along to the function
        :return: None
        """
        # mon, tue, wed, thu, fri, sat, sun & time
        days = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}
        if dday not in days:
            print('Not a valid day')
            return
        # Check if time of today is passed
        current = datetime.datetime.now()
        newtimer = datetime.datetime.strptime(
            "{}-{}-{} {}".format(str(current.year), str(current.month), str(current.day), dtime), "%Y-%m-%d %H:%M:%S")
        if (newtimer - datetime.datetime.now()).total_seconds() < 0:
            today = False
        else:
            today = True
        cday = current.weekday()
        diff = days[dday] - cday
        if diff > 0:
            add_days = diff
        elif (days[dday] - cday) == 0:
            if today:
                add_days = diff
            else:
                add_days = 8  # Date is of today but has passed time to it next week
        else:
            add_days = diff + 7
        newtimer = newtimer + datetime.timedelta(days=add_days)
        reccure = 'week'
        self.add_timer(newtimer, run, name, reccure, param)

    # def add_every_month(self):
        # ToDo
        # jan, feb, mar, apr, jun, jul, aug, sep, oct, nov, dec
        # day
        # time
        # None

    def wait_for_term(self):
        self.wthread.join()