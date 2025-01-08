import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const SignupPage = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        email: '',
        password: ''
    });
    const [error, setError] = useState('');

    const handleSignup = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('http://localhost:5001/users/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            if (!response.ok) throw new Error('ההרשמה נכשלה');

            navigate('/login');
        } catch (error) {
            setError(error.message);
        }
    };

    return (
        <div className="min-h-screen bg-black p-4 flex items-center justify-center">
            <div className="w-full max-w-md">
                <div className="bg-zinc-900 rounded-lg p-8">
                    <h2 className="text-white text-2xl mb-6 text-center">הרשמה</h2>
                    {error && (
                        <div className="bg-red-500 text-white p-3 rounded-lg mb-4">
                            {error}
                        </div>
                    )}
                    <form onSubmit={handleSignup} className="space-y-4">
                        <input
                            type="text"
                            value={formData.first_name}
                            onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                            placeholder="שם פרטי"
                            className="w-full bg-zinc-800 text-white border-none rounded-lg p-3"
                        />
                        <input
                            type="text"
                            value={formData.last_name}
                            onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                            placeholder="שם משפחה"
                            className="w-full bg-zinc-800 text-white border-none rounded-lg p-3"
                        />
                        <input
                            type="email"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            placeholder="אימייל"
                            className="w-full bg-zinc-800 text-white border-none rounded-lg p-3"
                        />
                        <input
                            type="password"
                            value={formData.password}
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                            placeholder="סיסמה"
                            className="w-full bg-zinc-800 text-white border-none rounded-lg p-3"
                        />
                        <button
                            type="submit"
                            className="w-full bg-[#4B0082] text-white py-3 px-6 rounded-lg"
                        >
                            הירשם
            </button>
                    </form>
                    <button
                        onClick={() => navigate('/login')}
                        className="w-full mt-4 text-white underline"
                    >
                        יש לך כבר חשבון? התחבר
          </button>
                </div>
            </div>
        </div>
    );
};

export default SignupPage;