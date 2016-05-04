import kingandassassins as KaA
import argparse

#class IAserver(KaA.KingAndAssassinsServer):
#    def __init__(self, verbose==False):
#        super().__init__('IA', 2, verbose=verbose)
#
#    def applymove(self, move):
#        tr

class IAclient(KaA.KingAndAssassinsClient):
    def __init__(self, name, role, server, verbose=False):
        print(server)
        super().__init__(server, verbose=verbose)
        self.__role= role
        #if self.__role == 'king':

        #elif self.__role== 'assassin':

        #else:
            #self.__quit()

    #def quit(self):


if __name__ == '__main__':
    #main parse
    parser= argparse.ArgumentParser(description='King and Assassins')
    subparsers= parser.add_subparsers(description='client', dest='component')
    #client parser
    client_parser = subparsers.add_parser('client')
    client_parser.add_argument('role')
    client_parser.add_argument('--name', default= 'Benj')
    client_parser.add_argument('--host', default= 'localhost')
    client_parser.add_argument('--port', default=5000)
    client_parser.add_argument('--v', '--verbose', action='store_true')
    args= parser.parse_args()

    if args.component == 'client':
        IAclient(args.name, args.role, (args.host, args.port), True)
    else:
        print('fbgnejtnb')
