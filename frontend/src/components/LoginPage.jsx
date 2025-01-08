import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const LoginPage = () => {
 const navigate = useNavigate();
 const [email, setEmail] = useState('');
 const [password, setPassword] = useState('');
 const [error, setError] = useState('');

 const handleLogin = async (e) => {
   e.preventDefault();
   try {
     const response = await fetch('http://localhost:5001/auth/login', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ email, password })
     });

     if (!response.ok) throw new Error('פרטי התחברות שגויים');
     
     const data = await response.json();
     localStorage.setItem('token', data.access_token);
     navigate('/');
   } catch (error) {
     setError(error.message);
   }
 };

 return (
   <div className="min-h-screen bg-black p-4 flex items-center justify-center">
     <div className="w-full max-w-md">
       <div className="bg-zinc-900 rounded-lg p-8">
         <h2 className="text-white text-2xl mb-6 text-center">התחברות</h2>
         {error && (
           <div className="bg-red-500 text-white p-3 rounded-lg mb-4">
             {error}
           </div>
         )}
         <form onSubmit={handleLogin} className="space-y-4">
           <input
             type="email"
             value={email}
             onChange={(e) => setEmail(e.target.value)}
             placeholder="אימייל"
             className="w-full bg-zinc-800 text-white border-none rounded-lg p-3"
           />
           <input
             type="password"
             value={password}
             onChange={(e) => setPassword(e.target.value)}
             placeholder="סיסמה"
             className="w-full bg-zinc-800 text-white border-none rounded-lg p-3"
           />
           <button 
             type="submit"
             className="w-full bg-[#4B0082] text-white py-3 px-6 rounded-lg"
           >
             התחבר
           </button>
         </form>
         <button 
           onClick={() => navigate('/signup')}
           className="w-full mt-4 text-white underline"
         >
           אין לך חשבון? הירשם
         </button>
       </div>
     </div>
   </div>
 );
};

export default LoginPage;