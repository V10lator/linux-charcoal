#!/usr/bin/bash

if [ "$EUID" -eq 0 ]; then
  echo "Please do not run as root"
  exit 1
fi

if ! pacman -Qq | grep -q '^linux-charcoal'; then
  echo "Charcoal kernel is not installed"
  exit 1
fi

# Use the originally installed neptune saved during install if available,
# otherwise fall back to the series from Charcoal's Replaces field
if [ -f /etc/charcoal-original-neptune ]; then
  _neptune=$(cat /etc/charcoal-original-neptune)
  echo "Restoring originally installed Neptune kernel: $_neptune"
else
  _neptune=$(pacman -Qi $(pacman -Qq | grep '^linux-charcoal' | grep -v headers | head -1) | grep '^Replaces' | tr ' ' '\n' | grep '^linux-neptune' | head -1)
  echo "Will reinstall: $_neptune (original not recorded, using Charcoal's Replaces field)"
fi

if [ -z "$_neptune" ]; then
  echo "Failed to detect Neptune kernel to restore"
  exit 1
fi

echo "Enabling dev mode (disables read-only filesystem and initialises keyring)..."
sudo steamos-devmode enable --no-prompt

echo "Removing Charcoal kernel..."
sudo pacman -Rsn --noconfirm $(pacman -Qq | grep '^linux-charcoal')

echo "Reinstalling Neptune kernel..."
sudo pacman -S --noconfirm "$_neptune"

echo "Updating GRUB..."
sudo grub-mkconfig -o /efi/EFI/steamos/grub.cfg

sudo rm -f /etc/charcoal-original-neptune

echo ""
echo "Done! Reboot to return to the Neptune kernel."
echo "Verify after reboot with: uname -a"
