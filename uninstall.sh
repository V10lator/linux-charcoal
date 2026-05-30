#!/usr/bin/bash

if [ "$EUID" -eq 0 ]; then
  echo "Please do not run as root"
  exit 1
fi

if ! pacman -Qq | grep -q '^linux-charcoal'; then
  echo "Charcoal kernel is not installed"
  exit 1
fi

echo "Detecting matching Neptune kernel..."
_neptune=$(pacman -Qi $(pacman -Qq | grep '^linux-charcoal' | grep -v headers | head -1) | awk '/^Replaces/{print $3}')

if [ -z "$_neptune" ]; then
  echo "Failed to detect matching Neptune kernel"
  exit 1
fi

echo "Will reinstall: $_neptune"

echo "Enabling dev mode (disables read-only filesystem and initialises keyring)..."
sudo steamos-devmode enable

echo "Removing Charcoal kernel..."
sudo pacman -Rsn --noconfirm $(pacman -Qq | grep '^linux-charcoal')

echo "Reinstalling Neptune kernel..."
sudo pacman -S --noconfirm "$_neptune"

echo "Updating GRUB..."
sudo grub-mkconfig -o /efi/EFI/steamos/grub.cfg

echo "Disabling dev mode..."
sudo steamos-devmode disable

echo ""
echo "Done! Reboot to return to the Neptune kernel."
echo "Verify after reboot with: uname -a"
