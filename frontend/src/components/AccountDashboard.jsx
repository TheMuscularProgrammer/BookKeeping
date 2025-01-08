import React, { useState, useEffect } from 'react';
import { transactionApi } from '../api/transactions';

const AccountDashboard = () => {
    const [amount, setAmount] = useState('');
    const [toAccount, setToAccount] = useState('');
    const [balance, setBalance] = useState(0);
    const [error, setError] = useState('');
    const date = new Date();

    const accountId = "YOUR_ACCOUNT_ID"; // יש להחליף או לקבל מהמצב הגלובלי
    const token = localStorage.getItem('token');

    const handleTransaction = async (type) => {
        try {
            setError('');
            let response;

            switch (type) {
                case 'deposit':
                    response = await transactionApi.deposit(accountId, Number(amount), token);
                    break;
                case 'withdraw':
                    response = await transactionApi.withdraw(accountId, Number(amount), token);
                    break;
                case 'transfer':
                    response = await transactionApi.transfer(accountId, Number(amount), toAccount, token);
                    break;
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Transaction failed');
            }

            setAmount('');
            setToAccount('');
            fetchBalance();
        } catch (error) {
            setError(error.message);
        }
    };

    const fetchBalance = async () => {
        try {
            const response = await transactionApi.getBalance(accountId, token);
            if (response.ok) {
                const data = await response.json();
                setBalance(data.balance);
            }
        } catch (error) {
            setError('Failed to fetch balance');
        }
    };

    useEffect(() => {
        fetchBalance();
    }, []);

    return (
        <div className="min-h-screen bg-black p-4">
            <div className="max-w-4xl mx-auto space-y-4">
                <div className="bg-zinc-900 rounded-lg p-4 flex items-start justify-between">
                    <div className="bg-zinc-800 rounded-lg p-2 w-24 text-center">
                        <div className="text-white text-sm">{date.toLocaleString('default', { month: 'long' })}</div>
                        <div className="text-white text-sm">{date.getFullYear()}</div>
                        <div className="text-white text-3xl font-bold">{date.getDate()}</div>
                    </div>
                    <div className="flex-grow mx-4">
                        <h1 className="text-white text-2xl px-4">חשבון בנק</h1>
                    </div>
                    <div className="bg-[#4B0082] rounded-lg px-6 py-2">
                        <span className="text-white text-xl">$ {balance}</span>
                    </div>
                </div>

                {error && (
                    <div className="bg-red-500 text-white p-3 rounded-lg">
                        {error}
                    </div>
                )}

                <div className="bg-zinc-900 p-6 rounded-lg">
                    <input
                        type="number"
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                        placeholder="סכום"
                        className="w-full bg-zinc-800 text-white border-none rounded-lg p-3 mb-4"
                    />

                    {toAccount !== undefined && (
                        <input
                            value={toAccount}
                            onChange={(e) => setToAccount(e.target.value)}
                            placeholder="מספר חשבון מקבל"
                            className="w-full bg-zinc-800 text-white border-none rounded-lg p-3 mb-4"
                        />
                    )}

                    <div className="flex gap-4 justify-center">
                        <button
                            onClick={() => handleTransaction('deposit')}
                            className="bg-[#4B0082] text-white py-3 px-6 rounded-lg flex-1"
                        >
                            הפקדה
           </button>
                        <button
                            onClick={() => handleTransaction('withdraw')}
                            className="bg-[#4B0082] text-white py-3 px-6 rounded-lg flex-1"
                        >
                            משיכה
           </button>
                        <button
                            onClick={() => handleTransaction('transfer')}
                            className="bg-[#4B0082] text-white py-3 px-6 rounded-lg flex-1"
                        >
                            העברה
           </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AccountDashboard;