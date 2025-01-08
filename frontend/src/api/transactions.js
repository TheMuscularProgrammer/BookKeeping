const API_URL = import.meta.env.VITE_API_URL;

export const transactionApi = {
  deposit: async (accountId, amount, token) => {
    return fetch(`${API_URL}/transactions/${accountId}/deposit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ amount })
    });
  },

  withdraw: async (accountId, amount, token) => {
    return fetch(`${API_URL}/transactions/${accountId}/withdraw`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ amount })
    });
  },

  transfer: async (accountId, amount, toAccountId, token) => {
    return fetch(`${API_URL}/transactions/${accountId}/transfer`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ 
        amount,
        to_account_id: toAccountId
      })
    });
  },

  getBalance: async (accountId, token) => {
    return fetch(`${API_URL}/transactions/${accountId}/balance`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
  }
};