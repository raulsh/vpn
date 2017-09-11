#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Options:
[-s | --start]
[-k | --kill]
[-r | --restart]
[-n | --noicon]              - no icon in tray, log to stdout
[-t | --textonly]            - text mode
[-d | --debug]               - debug mode
[-h | --help | <none>]

Configuration in <script_name>.secret, log in <script_name>.log in scripts
home dir.
Warning! Option -d causes writes out full pexpect log (includes username
and password(s)) to stdout.
"""

import pexpect
import getopt
from vpn_lib import *


class forticlient:
    def __init__(self):
        self.__noicon = myVPN.noicon
        self.__textonly = myVPN.textonly
        self.__debug = myVPN.debug
        if self.__textonly or self.__debug:
            self.__logFile = sys.stdout
        else:
            self.__logFile = open(homeDir + "/" + scriptName + ".log", "w")
        myVPN.checkPidFile()
        try:
            self.__vpnServer = '"' + myVPN.config.get("vpn", "vpnServer") + '"'
            self.__vpnUser   = '"' + myVPN.config.get("vpn", "vpnUser") + '"'
            self.__vpnPasswd = myVPN.config.get("vpn", "vpnPasswd")

            self.__cmd = myVPN.config.get("vpn", "forticlient") + " "
        except:
            msg = "Bad credentials file format"
            self.__logFile.write(msg + ":\n" + traceback.format_exc())
            if not self.__textonly and not self.__debug:
                n = notify2.Notification(msg, "Check file: " + scriptName + ".log", errorIcon)
                n.set_urgency(2)
                n.show()
            raise

        self.__cmd += "--server " + self.__vpnServer + " --vpnuser " + self.__vpnUser + " "
        self.__cmd += "--keepalive "

    def startVPN(self):
        self.__logFile.write("spawning:\n" + self.__cmd + "\n")
        self.__logFile.write(80 * "-" + "\n")
        msg = "Setting up connection " + scriptName
        if not self.__textonly and not self.__debug:
            n = notify2.Notification(msg, "", connectingIcon)
            n.set_urgency(0)
            n.show()
        else:
            print msg

        myVPN.sysCmds("preVPNstart")
        try:
            vpn = pexpect.spawn(self.__cmd)
            if self.__debug:
                vpn.logfile = self.__logFile
            else:
                vpn.logfile_read = self.__logFile

            if 0 == vpn.expect_exact("Password for VPN:"): vpn.sendline(s=self.__vpnPasswd)
            if 0 == vpn.expect_exact("Would you like to connect to this server? (Y/N)"): vpn.sendline(s="y")

            if 0 == vpn.expect(["Tunnel running"], timeout=60):
                file(homeDir + "/" + scriptName + ".pid", "w").write(str(os.getpid()))
                myVPN.sysCmds("postVPNstart")
                msg = "Connection " + scriptName + " ready"
                if not self.__textonly and not self.__debug:
                    n.update(msg, "" if self.__noicon == True else "Right click to close", connectionOKIcon)
                    n.set_urgency(1)
                    n.show()
                    if not self.__noicon :
                        myVPN.set_icon(homeDir + "/" + scriptName + ".png")
                        gtk.main()
                else:
                    print msg
                vpn.wait()

        except pexpect.EOF:
            self.__logFile.write("pexpect: EOF\n")
            if not self.__textonly and not self.__debug:
                n.update("pexpect: EOF", "", errorIcon)
        except pexpect.TIMEOUT:
            self.__logFile.write("Connection timeout\n")
            if not self.__textonly and not self.__debug:
                n.update("Connection timeout", "", errorIcon)
        except:
            self.__logFile.write("Unhandled error: " + traceback.format_exc())
            if not self.__textonly and not self.__debug:
                n.update("Unhandled error", traceback.format_exc(), errorIcon)
            raise
        finally:
            if not self.__textonly and not self.__debug:
                n.set_urgency(2)
                n.show()


def main(argv):

    def usage():
        print(globals()['__doc__'])
        sys.exit(2)

    if len(argv) == 0: usage()

    try:
        opts, args = getopt.getopt(argv, "skrnitdh",
                                   ["start",
                                    "kill",
                                    "restart",
                                    "noicon",
                                    "textonly",
                                    "debug",
                                    "help"])
    except getopt.GetoptError: usage()

    noicon = textonly = debug = False
    for opt, arg in opts:
        if   opt in ("-n", "--noicon"):
            noicon = True
        elif opt in ("-t", "--textonly"):
            textonly = True
        elif opt in ("-d", "--debug"):
            debug = True
        elif opt in ("-h", "--help"):
            usage()

    global myVPN
    myVPN = vpn_lib(homeDir, scriptName, textonly, debug, noicon)
    for opt, arg in opts:
        if opt in ("-k", "--kill"):
            myVPN.killVpn()
        elif opt in ("-s", "--start"):
            fc = forticlient()
            fc.startVPN()
        elif opt in ("-r", "--restart"):
            myVPN.killVpn()
            time.sleep(1)
            fc = forticlient()
            fc.startVPN()

    return 0


if __name__ == "__main__":
    global scriptName, homeDir
    scriptName = os.path.basename(sys.argv[0])[0:-3]
    homeDir = os.path.dirname(sys.argv[0])
    main(sys.argv[1:])

