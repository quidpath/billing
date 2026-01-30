#!/bin/bash

# Make all shell scripts executable

echo "Making scripts executable..."

chmod +x connect-networks.sh
chmod +x fix-billing-linux.sh
chmod +x billing/check-billing-logs.sh
chmod +x billing/quick-diagnose.sh

echo "✅ All scripts are now executable"
echo ""
echo "You can now run:"
echo "  ./connect-networks.sh"
echo "  ./fix-billing-linux.sh"
echo "  ./billing/quick-diagnose.sh"
echo ""
