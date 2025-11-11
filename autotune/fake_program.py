import sys

def main():
    if "--help" in sys.argv:
        print("Uso: fake_program [float] [float]")
        return

    args = sys.argv[1:]
    if not args:
        print("0")
        return

    x, y = map(float, args)
    print((x - 3)**2 + (y + 2)**2)

if __name__ == "__main__":
    main()
