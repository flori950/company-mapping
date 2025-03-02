from colorama import Fore


class Logger:
    verbose = False

    @staticmethod
    def log(message):
        print(Fore.WHITE + message)
        Fore.RESET

    @staticmethod
    def error(message):
        print(Fore.RED + message)
        Fore.RESET

    @staticmethod
    def warning(message):
        print(Fore.YELLOW + message)
        Fore.RESET

    @staticmethod
    def info(message):
        print(Fore.BLUE + message)
        Fore.RESET

    @staticmethod
    def success(message):
        print(Fore.GREEN + message)
        Fore.RESET

    @staticmethod
    def debug(message):
        if Logger.verbose:
            print(Fore.MAGENTA + message)
            Fore.RESET
