// To make sure shares count won't go below 0 in buy and sell
function validateSharesInput(input) {
    // Ensure the input value is a non-negative integer
    var currentShares = parseInt(input.value, 10) || 0;
    input.value = Math.max(currentShares, 0);
}

// To make sure shares count won't go below 0 in cash
function validateCash(cashInput) {
    var currentCash = parseFloat(cashInput.value, 10) || 0;
    cashInput.value = Math.max(currentCash, 0.00);
}