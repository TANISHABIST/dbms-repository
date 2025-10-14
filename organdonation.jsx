import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { initializeApp } from 'firebase/app';
import { getAuth, signInAnonymously, signInWithCustomToken, onAuthStateChanged } from 'firebase/auth';
import {
  getFirestore, collection, onSnapshot, doc, updateDoc, getDoc,
  writeBatch, serverTimestamp, setLogLevel
} from 'firebase/firestore';
import {
  Heart, Shield, User as UserIcon, Building2, LayoutDashboard, Clock, CheckCircle
} from 'lucide-react';

const appId = 'default-organ-donation-app-id';
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "your-app.firebaseapp.com",
  projectId: "your-app-id",
  storageBucket: "your-app.appspot.com",
  messagingSenderId: "1234567890",
  appId: "YOUR_APP_ID"
};
const initialAuthToken = '';
setLogLevel('debug');

const retryOperation = async (operation, maxRetries = 5) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      const delay = Math.pow(2, i) * 1000 + Math.random() * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
};

const publicDataPath = (collectionName) => `/artifacts/${appId}/public/data/${collectionName}`;

const initialDonor = { id: 'donor-1', name: 'Alex Johnson', bloodType: 'A+', organs: ['Kidney', 'Liver'], status: 'Registered', registeredAt: serverTimestamp() };
const initialRecipient = { id: 'recipient-1', name: 'Maria Garcia', bloodType: 'A+', organNeeded: 'Kidney', urgency: 'High', status: 'Waiting' };
const initialHospital = { id: 'hospital-1', name: 'Global Transplant Center', contact: 'Dr. Lee', registeredAt: serverTimestamp(), city: 'Metropolis' };
const initialAdmin = { id: 'admin-1', name: 'Portal Admin', email: 'admin@portal.com' };

const Header = ({ currentRole, onLogout }) => (
  <header className="bg-white shadow-lg p-4 sticky top-0 z-10">
    <div className="flex justify-between items-center max-w-7xl mx-auto">
      <div className="flex items-center space-x-2">
        <Heart className="text-red-600 h-8 w-8" />
        <h1 className="text-2xl font-extrabold text-gray-800 tracking-tight font-inter">
          LifeLink Portal
        </h1>
      </div>
      {currentRole && (
        <div className="flex items-center space-x-4">
          <span className={`px-3 py-1 text-sm font-semibold rounded-full capitalize 
            ${currentRole === 'admin' ? 'bg-purple-100 text-purple-700' : 
            currentRole === 'hospital' ? 'bg-indigo-100 text-indigo-700' :
            currentRole === 'donor' ? 'bg-green-100 text-green-700' :
            'bg-blue-100 text-blue-700'}`}>
            Role: {currentRole}
          </span>
          <button
            onClick={onLogout}
            className="bg-red-500 hover:bg-red-600 text-white font-medium py-2 px-4 rounded-lg transition duration-300 shadow-md"
          >
            Logout
          </button>
        </div>
      )}
    </div>
  </header>
);

const DashboardCard = ({ title, value, icon: Icon, colorClass, children }) => (
  <div className={`p-6 rounded-xl shadow-xl transition duration-300 hover:shadow-2xl ${colorClass} bg-white border border-gray-100`}>
    <div className="flex items-center justify-between">
      <h3 className="text-lg font-semibold text-gray-600">{title}</h3>
      {Icon && <Icon className={`h-8 w-8 opacity-70 ${colorClass.replace('bg-', 'text-')}`} />}
    </div>
    {value && <p className="mt-2 text-4xl font-extrabold text-gray-900">{value}</p>}
    {children && <div className="mt-4">{children}</div>}
  </div>
);

const RoleSelector = ({ onSelectRole }) => {
  const roles = [
    { id: 'donor', name: 'Donor', icon: Heart, desc: 'Manage your registration status.' },
    { id: 'recipient', name: 'Recipient', icon: UserIcon, desc: 'Check your waiting list status.' },
    { id: 'hospital', name: 'Hospital', icon: Building2, desc: 'Manage patient and donor data.' },
    { id: 'admin', name: 'Administrator', icon: Shield, desc: 'Oversee system operations.' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        <h2 className="text-3xl font-bold text-center text-gray-800 mb-8">Select Your Portal Access</h2>
        <div className="grid md:grid-cols-2 gap-6">
          {roles.map((role) => (
            <div
              key={role.id}
              onClick={() => onSelectRole(role.id)}
              className="bg-white p-6 rounded-xl shadow-lg border-2 border-transparent hover:border-red-500 transition duration-300 cursor-pointer"
            >
              <role.icon className="h-8 w-8 text-red-600 mb-3" />
              <h3 className="text-xl font-bold text-gray-900">{role.name} Portal</h3>
              <p className="text-gray-500 mt-1">{role.desc}</p>
              <button className="mt-4 text-sm font-semibold text-red-600 hover:text-red-700">
                Proceed →
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const App = () => {
  const [currentRole, setCurrentRole] = useState(null);
  const [db, setDb] = useState(null);
  const [auth, setAuth] = useState(null);
  const [userId, setUserId] = useState(null);
  const [isAuthReady, setIsAuthReady] = useState(false);
  const [allDonors, setAllDonors] = useState([]);
  const [allRecipients, setAllRecipients] = useState([]);
  const [allHospitals, setAllHospitals] = useState([]);
  const appRef = useRef(null);

  useEffect(() => {
    if (Object.keys(firebaseConfig).length > 0 && !appRef.current) {
      try {
        const initializedApp = initializeApp(firebaseConfig);
        const authInstance = getAuth(initializedApp);
        const dbInstance = getFirestore(initializedApp);
        setDb(dbInstance);
        setAuth(authInstance);
        appRef.current = initializedApp;
        const unsubscribe = onAuthStateChanged(authInstance, (user) => {
          if (user) {
            setUserId(user.uid);
          } else {
            signInAnonymously(authInstance).then((cred) => {
              setUserId(cred.user.uid);
            });
          }
          setIsAuthReady(true);
        });
        if (initialAuthToken) {
          signInWithCustomToken(authInstance, initialAuthToken).catch(console.error);
        }
        return () => unsubscribe();
      } catch (e) {
        console.error(e);
      }
    }
  }, [initialAuthToken]);

  const handleLogout = () => setCurrentRole(null);

  return (
    <div className="min-h-screen bg-gray-50 font-inter">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');
        .font-inter { font-family: 'Inter', sans-serif; }
      `}</style>
      <Header currentRole={currentRole} onLogout={handleLogout} />
      <main className="py-10">
        {!currentRole ? <RoleSelector onSelectRole={setCurrentRole} /> : <div className="text-center p-8">Dashboard for {currentRole}</div>}
      </main>
      <footer className="p-4 text-center text-sm text-gray-500 border-t mt-10">
        LifeLink Organ Donation Portal | Secure Access ID: {userId || 'Authenticating...'}
      </footer>
    </div>
  );
};

export default App;