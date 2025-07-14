#!/bin/bash
# Script to update currency format across all components

echo "Updating currency formats across all components..."

# Components to update
COMPONENTS=(
  "Inventory.js"
  "Shop.js" 
  "GiftModal.js"
  "MoveSelectionStep.js"
  "UserManagement.js"
  "BetsManagement.js"
  "HeaderPortfolio.js"
  "GameResult.js"
  "GameHistory.js"
  "JoinBattleModal.js"
)

# Update imports in each component
for component in "${COMPONENTS[@]}"; do
  file="/app/frontend/src/components/$component"
  if [ -f "$file" ]; then
    echo "Updating $component..."
    
    # Add new imports if not already present
    if ! grep -q "formatDollarAmount\|formatGemValue" "$file"; then
      sed -i 's/import { formatCurrencyWithSymbol/import { formatCurrencyWithSymbol, formatDollarAmount, formatGemValue/' "$file"
    fi
    
    echo "  - Updated imports in $component"
  else
    echo "  - $component not found, skipping..."
  fi
done

echo "Currency format updates completed!"