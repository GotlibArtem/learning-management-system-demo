document.addEventListener('DOMContentLoaded', () => {
    const amountInput = document.getElementById('id_amount');
    const typeInput = document.getElementById('id_transaction_type');
    const futureBalanceSpan = document.getElementById('future-balance');

    if (!amountInput || !typeInput || !futureBalanceSpan) return;

    futureBalanceSpan.dataset.orig = futureBalanceSpan.textContent;

    const parseBalance = (value) => {
        const parsed = parseInt(value, 10);
        return isNaN(parsed) ? 0 : parsed;
    };

    const calculateFutureBalance = () => {
        const currentBalance = parseBalance(futureBalanceSpan.dataset.orig);
        const amount = parseBalance(amountInput.value);
        const transactionType = typeInput.value;

        let newBalance = currentBalance;

        if (transactionType === 'admin_earned') {
            newBalance += Math.abs(amount);
        } else if (transactionType === 'admin_spent') {
            newBalance -= Math.abs(amount);
        }

        futureBalanceSpan.textContent = newBalance;
    };

    amountInput.addEventListener('input', calculateFutureBalance);
    typeInput.addEventListener('change', calculateFutureBalance);
});
