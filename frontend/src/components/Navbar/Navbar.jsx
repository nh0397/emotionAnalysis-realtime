// Navbar.jsx
import React from 'react';
import './Navbar.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlus } from '@fortawesome/free-solid-svg-icons';
import './Navbar.css'
import Logo from  './Logo.webp'
function Navbar(props) {

    return (
        <div className="navbar-container">
            <div className="navbar-left">
               <img src={Logo} alt="App Logo" className="app-logo" />
            </div>
            <div className="navbar-right">
                <div className='app-name'>Visual Analytics Support for Exploring People's Emotion Towards Events using Tweet(X) Data</div>
            </div>
        </div>
    );
}

export default Navbar;
