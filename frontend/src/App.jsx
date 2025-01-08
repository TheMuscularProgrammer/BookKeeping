import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './components/LoginPage';
import SignupPage from './components/SignupPage';
import AccountDashboard from './components/AccountDashboard';

function App() {
 const isAuthenticated = !!localStorage.getItem('token');

 return (
   <BrowserRouter>
     <Routes>
       <Route path="/login" element={!isAuthenticated ? <LoginPage /> : <Navigate to="/" />} />
       <Route path="/signup" element={!isAuthenticated ? <SignupPage /> : <Navigate to="/" />} />
       <Route path="/" element={isAuthenticated ? <AccountDashboard /> : <Navigate to="/login" />} />
     </Routes>
   </BrowserRouter>
 );
}

export default App;