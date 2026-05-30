#!/usr/bin/bash

if [ "$EUID" -eq 0 ]; then
  echo "Please do not run as root"
  exit 1
fi

echo "Fetching latest Charcoal release..."
RELEASE_JSON=$(curl -s https://api.github.com/repos/V10lator/linux-charcoal/releases/latest)
PKG_URL=$(echo "$RELEASE_JSON" | grep "browser_download_url" | grep -v "headers" | grep "x86_64.pkg.tar.zst" | cut -d '"' -f 4)
HEADERS_URL=$(echo "$RELEASE_JSON" | grep "browser_download_url" | grep "headers" | grep "x86_64.pkg.tar.zst" | cut -d '"' -f 4)

if [ -z "$PKG_URL" ] || [ -z "$HEADERS_URL" ]; then
  echo "Failed to fetch release URLs"
  exit 1
fi

echo "Downloading kernel..."
curl -L "$PKG_URL" -o /tmp/linux-charcoal.pkg.tar.zst

echo "Downloading headers..."
curl -L "$HEADERS_URL" -o /tmp/linux-charcoal-headers.pkg.tar.zst

echo "Disabling read-only filesystem..."
sudo steamos-readonly disable

echo "Removing existing Neptune kernel..."
pacman -Qq 'linux-neptune*' 2>/dev/null | xargs -r sudo pacman -Rns --noconfirm

echo "Installing Charcoal kernel..."
sudo pacman -U --noconfirm /tmp/linux-charcoal.pkg.tar.zst /tmp/linux-charcoal-headers.pkg.tar.zst

echo "Updating GRUB..."
sudo grub-mkconfig -o /efi/EFI/steamos/grub.cfg

echo "Re-enabling read-only filesystem..."
sudo steamos-readonly enable

echo "Cleaning up..."
rm -f /tmp/linux-charcoal*.pkg.tar.zst

echo ""
echo "Done! Reboot to use the Charcoal kernel."
echo "Verify after reboot with: uname -a"
