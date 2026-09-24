import React, { useState, useEffect } from 'react';
import { UserProfile } from '../types';
import { mobileApiClient } from '../api/client';
import { User, Mail, Globe, Clock } from 'lucide-react';

export const ProfileView: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    mobileApiClient.getUserProfile().then(setProfile);
  }, []);

  return (
    <div className="mobile-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Identity & Personal Profile
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 03 Identity & Companion Profile</span>
      </div>

      {profile && (
        <div className="glass-panel" style={{ padding: '20px', borderRadius: 'var(--radius-lg)', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--primary) 0%, var(--accent-purple) 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '20px', fontWeight: 800 }}>
              U
            </div>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: 'var(--text-main)' }}>{profile.name}</h3>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{profile.email}</span>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', borderTop: '1px solid var(--border-glass)', paddingTop: '12px', fontSize: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
              <Globe size={14} />
              <span>Language: <strong style={{ color: 'var(--text-main)' }}>{profile.preferred_language}</strong></span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
              <Clock size={14} />
              <span>Timezone: <strong style={{ color: 'var(--text-main)' }}>{profile.time_zone}</strong></span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
