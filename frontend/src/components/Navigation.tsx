import React, { useState } from 'react';
import { 
  MdDashboard, 
  MdUpload, 
  MdLogout,
  MdPerson
} from 'react-icons/md';
import styles from './Navigation.module.css';
import ConfirmationModal from './ConfirmationModal';
import logo from '../logo.png';
import { doLogout } from '../keycloak';

interface NavigationProps {
  currentPage: string;
  onPageChange: (page: string) => void;
  userName?: string;
}

export const Navigation: React.FC<NavigationProps> = ({ 
  currentPage, 
  onPageChange, 
  userName = "BookLatte"
}) => {
  const [showLogoutModal, setShowLogoutModal] = useState(false);

  const navigationItems = [
    { id: 'dashboard', label: 'Dashboard', icon: MdDashboard },
    { id: 'upload', label: 'Data Upload', icon: MdUpload },
  ];

  const handleLogoutClick = () => {
    setShowLogoutModal(true);
  };

  const handleLogoutConfirm = () => {
    setShowLogoutModal(false);
    
    // Clear any local session data
    localStorage.clear();
    sessionStorage.clear();
    
    // Keycloak logout
    doLogout();
  };

  const handleLogoutCancel = () => {
    setShowLogoutModal(false);
  };

  return (
    <>
      {/* Top Navigation Bar */}
      <nav className={styles.topNav}>
        <div className={styles.topNavLeft}>
          <div className={styles.logo}>
            <img src={logo} alt="BookLatte Logo" className={styles.logoImage} />
            <h2>BookLatte Analytics</h2>
          </div>
        </div>
        
        <div className={styles.topNavRight}>
          <div className={styles.userProfile}>
            <MdPerson />
            <span>{userName}</span>
          </div>
          
          <button 
            className={styles.logoutButton}
            onClick={handleLogoutClick}
            aria-label="Logout"
          >
            <MdLogout />
          </button>
        </div>
      </nav>

      {/* Sidebar Navigation */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <h3>MENU</h3>
        </div>
        
        <nav className={styles.sidebarNav}>
          {navigationItems.map((item) => {
            const IconComponent = item.icon;
            return (
              <button
                key={item.id}
                className={`${styles.navItem} ${currentPage === item.id ? styles.navItemActive : ''}`}
                onClick={() => onPageChange(item.id)}
              >
                <IconComponent className={styles.navIcon} />
                <span className={styles.navLabel}>{item.label}</span>
              </button>
            );
          })}
        </nav>
        
        <div className={styles.sidebarFooter}>
          <div className={styles.sidebarSection}>
            <h4>OTHERS</h4>
            <button 
              className={styles.navItem}
              onClick={handleLogoutClick}
            >
              <MdLogout className={styles.navIcon} />
              <span className={styles.navLabel}>Log Out</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Logout Confirmation Modal */}
      <ConfirmationModal
        isOpen={showLogoutModal}
        title="Logout Confirmation"
        message="Are you sure you want to logout?"
        confirmText="OK"
        cancelText="Cancel"
        onConfirm={handleLogoutConfirm}
        onCancel={handleLogoutCancel}
        variant="default"
      />
    </>
  );
};

export default Navigation;