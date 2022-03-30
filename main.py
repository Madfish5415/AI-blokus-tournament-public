import sys

from game import *


def main():

    if len(sys.argv) < 2:
        exit(84)

    ply_nb = int(sys.argv[1])

    if ply_nb != 2 and ply_nb != 4:
        exit(84)

    if len(sys.argv) != 2 + ply_nb:
        exit(84)

    game = Game(ply_nb, sys.argv)

    for i in range(ply_nb):
        game.set_player_script(i, sys.argv[2 + i])

    asyncio.run(game.run())
    return


if __name__ == '__main__':
    print(os.getcwd())

    main()
