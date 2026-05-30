#!/usr/bin/bash

if [ "$EUID" -eq 0 ]; then
  echo "Please do not run as root"
  exit 1
fi

if ! pacman -Qq 'linux-charcoal*' &>/dev/null; then
  echo "Charcoal kernel is not installed"
  exit 1
fi

echo "Detecting matching Neptune kernel..."
_neptune=$(pacman -Qi $(pacman -Qq 'linux-charcoal*' | grep -v headers | head -1) | awk '/^Replaces/{print $3}')

if [ -z "$_neptune" ]; then
  echo "Failed to detect matching Neptune kernel"
  exit 1
fi

echo "Will reinstall: $_neptune"

echo "Disabling read-only filesystem..."
sudo steamos-readonly disable

echo "Removing Charcoal kernel..."
sudo pacman -Rsn --noconfirm $(pacman -Qq 'linux-charcoal*')

echo "Reinstalling Neptune kernel..."
sudo pacman -S --noconfirm "$_neptune"

echo "Updating GRUB..."
sudo grub-mkconfig -o /efi/EFI/steamos/grub.cfg

echo "Re-enabling read-only filesystem..."
sudo steamos-readonly enable

echo ""
echo "Done! Reboot to return to the Neptune kernel."
echo "Verify after reboot with: uname -a"
