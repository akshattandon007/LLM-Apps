"""passvault CLI - entry point for the passvault command."""

import argparse
import getpass
import sys

from . import vault, generator, utils


def get_password(confirm=False):
    pw = getpass.getpass("Master password: ")
    if confirm:
        pw2 = getpass.getpass("Confirm master password: ")
        if pw != pw2:
            print("Error: passwords do not match", file=sys.stderr)
            sys.exit(1)
    if len(pw) < 8:
        print("Warning: master password is short (min 8 chars)", file=sys.stderr)
    return pw


def cmd_init(args):
    if vault.vault_exists():
        print(f"Vault exists at {vault.VAULT_PATH}")
        ans = input("Overwrite? [y/N]: ").strip().lower()
        if ans != "y":
            print("Aborted.")
            return
    pw = get_password(confirm=True)
    path = vault.init_vault(pw)
    print(f"Vault created at {path}")
    print("Remember your master password - it cannot be recovered!")


def cmd_add(args):
    pw = get_password()
    name = args.name
    username = args.username or input("Username: ").strip()
    pwd = getpass.getpass("Password (blank = auto-generate): ")
    if not pwd:
        pwd = generator.generate_password()
        print(f"Generated: {pwd}")
        utils.copy_to_clipboard(pwd)
        print("(copied to clipboard)")
    entry = vault.add_entry(pw, name, username, pwd, args.url, args.notes)
    print(f"Entry {name!r} added (id: {entry['id']})")


def cmd_get(args):
    pw = get_password()
    entry = vault.get_entry(pw, args.name)
    if entry is None:
        print(f"Entry {args.name!r} not found")
        return
    utils.print_entry(entry)
    utils.copy_to_clipboard(entry["password"])
    print("(password copied to clipboard)")


def cmd_list(args):
    pw = get_password()
    entries = vault.list_entries(pw)
    if not entries:
        print("No entries in vault.")
        return
    print()
    print("Name                      Username              URL")
    print("-" * 80)
    for e in entries:
        nm = e["name"][:24]
        un = e.get("username", "")[:19]
        ul = e.get("url", "")[:34]
        print(f"{nm:25} {un:20} {ul:35}")


def cmd_search(args):
    pw = get_password()
    results = vault.search_entries(pw, args.query)
    if not results:
        print(f"No entries matching {args.query!r}")
        return
    print()
    print("Name                      Username              URL")
    print("-" * 80)
    for e in results:
        nm = e["name"][:24]
        un = e.get("username", "")[:19]
        ul = e.get("url", "")[:34]
        print(f"{nm:25} {un:20} {ul:35}")


def cmd_rm(args):
    pw = get_password()
    entry = vault.get_entry(pw, args.name)
    if entry is None:
        print(f"Entry {args.name!r} not found")
        return
    print("Entry to delete:")
    utils.print_entry(entry, show_password=False)
    ans = input("\nDelete {}? [y/N]: ".format(entry["name"])).strip().lower()
    if ans != "y":
        print("Aborted.")
        return
    if vault.delete_entry(pw, args.name):
        print(f"Entry {args.name!r} deleted")
    else:
        print(f"Entry {args.name!r} not found")


def cmd_generate(args):
    pwd = generator.generate_password(
        length=args.length,
        use_symbols=not args.no_symbols,
        use_digits=not args.no_digits,
    )
    print(pwd)
    utils.copy_to_clipboard(pwd)
    s = generator.password_strength(pwd)
    print(f"Strength: {s['grade']} ({s['entropy_bits']} bits)")


def cmd_passphrase(args):
    phrase = generator.generate_passphrase(
        word_count=args.words, separator=args.sep,
    )
    print(phrase)
    utils.copy_to_clipboard(phrase)
    print("Passphrase copied to clipboard")


def cmd_strength(args):
    pwd = args.password or getpass.getpass("Password to analyze: ")
    r = generator.password_strength(pwd)
    print(f"  Length:    {r['length']}")
    print(f"  Uppercase: {'Yes' if r['has_uppercase'] else 'No'}")
    print(f"  Lowercase: {'Yes' if r['has_lowercase'] else 'No'}")
    print(f"  Digits:    {'Yes' if r['has_digit'] else 'No'}")
    print(f"  Symbols:   {'Yes' if r['has_symbol'] else 'No'}")
    print(f"  Entropy:   {r['entropy_bits']} bits")
    print(f"  Grade:     {r['grade']}")


def main():
    parser = argparse.ArgumentParser(
        prog="passvault",
        description="Local encrypted CLI password manager. No cloud. No signup.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")

    p = sub.add_parser("add")
    p.add_argument("name")
    p.add_argument("-u", "--username", default="")
    p.add_argument("--url", default="")
    p.add_argument("--notes", default="")

    p = sub.add_parser("get")
    p.add_argument("name")

    sub.add_parser("list")

    p = sub.add_parser("search")
    p.add_argument("query")

    p = sub.add_parser("rm")
    p.add_argument("name")

    p = sub.add_parser("generate")
    p.add_argument("--length", type=int, default=20)
    p.add_argument("--no-symbols", action="store_true")
    p.add_argument("--no-digits", action="store_true")

    p = sub.add_parser("passphrase")
    p.add_argument("--words", type=int, default=5)
    p.add_argument("--sep", default="-")

    p = sub.add_parser("strength")
    p.add_argument("password", nargs="?")

    args = parser.parse_args()

    handlers = {
        "init": cmd_init,
        "add": cmd_add,
        "get": cmd_get,
        "list": cmd_list,
        "search": cmd_search,
        "rm": cmd_rm,
        "generate": cmd_generate,
        "passphrase": cmd_passphrase,
        "strength": cmd_strength,
    }

    handlers[args.cmd](args)


if __name__ == "__main__":
    main()
