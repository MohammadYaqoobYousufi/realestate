// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";
// import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDGqsZjyWmOgXCzFUR_ubLwOb_I7w91IEY",
  authDomain: "real-estate-7f4a7.firebaseapp.com",
  projectId: "real-estate-7f4a7",
  storageBucket: "real-estate-7f4a7.firebasestorage.app",
  messagingSenderId: "185159663307",
  appId: "1:185159663307:web:d6e01d10b34d523cb4654e",
  measurementId: "G-D6QFFMQ3SR"
};

// Initialize Firebase
initializeApp(firebaseConfig);
export const db = getFirestore();
// const analytics = getAnalytics(app);