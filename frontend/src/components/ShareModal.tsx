'use client';

import { useState } from 'react';
import { Itinerary } from '@/types';
import { formatCost } from '@/utils/currency';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  itinerary: Itinerary;
  onDownloadPdf?: () => void;
  isDownloadingPdf?: boolean;
}

export default function ShareModal({
  isOpen,
  onClose,
  itinerary,
  onDownloadPdf,
  isDownloadingPdf = false,
}: Props) {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !itinerary) return null;

  const dest = itinerary.trip_request?.destination || 'Trip';
  const numDays = itinerary.days?.length || 0;
  const cost = itinerary.total_cost_estimate_usd;
  const costFormatted = cost ? formatCost(cost, dest) : 'Free';

  // Construct public share URL
  const origin = typeof window !== 'undefined' ? window.location.origin : 'https://wanderai.app';
  const shareUrl = `${origin}/trip/${itinerary.id}`;

  const shareText = `Check out my ${numDays}-Day custom itinerary to ${dest} planned with WanderAI! 🗺️✨\n${shareUrl}`;

  const handleCopy = async () => {
    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(shareUrl);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = shareUrl;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.warn('Clipboard copy error:', err);
    }
  };

  const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(shareText)}`;
  const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(`Check out my ${numDays}-day ${dest} trip planned with @WanderAI!`)}&url=${encodeURIComponent(shareUrl)}`;
  const emailUrl = `mailto:?subject=${encodeURIComponent(`WanderAI ${numDays}-Day ${dest} Travel Itinerary`)}&body=${encodeURIComponent(shareText)}`;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(4, 14, 31, 0.75)',
        backdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'linear-gradient(135deg, #0d192c 0%, #15253d 100%)',
          border: '1px solid rgba(0, 219, 231, 0.25)',
          borderRadius: '16px',
          padding: '24px',
          width: '100%',
          maxWidth: '480px',
          color: '#ffffff',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6), 0 0 30px rgba(0, 219, 231, 0.1)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '20px' }}>🔗</span>
            <h3 style={{ fontFamily: 'Playfair Display, serif', fontSize: '20px', fontWeight: 700, margin: 0 }}>
              Share Your Itinerary
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              border: 'none',
              borderRadius: '50%',
              width: '32px',
              height: '32px',
              color: '#94a3b8',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '14px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Trip Preview Pill */}
        <div
          style={{
            background: 'rgba(4, 14, 31, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '10px',
            padding: '12px 14px',
            marginBottom: '18px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '15px', fontWeight: 600, color: '#00DBE7', marginBottom: '2px' }}>
              {dest}
            </div>
            <div style={{ fontSize: '12px', color: '#94a3b8' }}>
              {numDays} Days · {itinerary.trip_request?.travel_style || 'Balanced'}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>Est. Cost</div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#E8A838' }}>{costFormatted}</div>
          </div>
        </div>

        {/* Copy Link Input */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '6px', fontWeight: 500 }}>
            Public Shareable Link
          </label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              readOnly
              value={shareUrl}
              style={{
                flex: 1,
                background: '#040e1f',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                borderRadius: '8px',
                padding: '8px 12px',
                color: '#d8e3fb',
                fontSize: '13px',
                fontFamily: 'monospace',
                outline: 'none',
              }}
            />
            <button
              onClick={handleCopy}
              style={{
                background: copied ? '#10B981' : '#00DBE7',
                color: '#040e1f',
                border: 'none',
                borderRadius: '8px',
                padding: '0 16px',
                fontWeight: 700,
                fontSize: '13px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              {copied ? '✅ Copied' : '📋 Copy'}
            </button>
          </div>
        </div>

        {/* Social Share Buttons */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ fontSize: '12px', color: '#94a3b8', display: 'block', marginBottom: '8px', fontWeight: 500 }}>
            Share directly via
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
            <a
              href={whatsappUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                background: 'rgba(37, 211, 102, 0.15)',
                border: '1px solid rgba(37, 211, 102, 0.3)',
                borderRadius: '8px',
                padding: '10px 8px',
                color: '#25D366',
                textAlign: 'center',
                textDecoration: 'none',
                fontSize: '12px',
                fontWeight: 600,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '4px',
                transition: 'all 0.2s ease',
              }}
            >
              <span style={{ fontSize: '18px' }}>💬</span>
              WhatsApp
            </a>
            <a
              href={twitterUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                background: 'rgba(29, 161, 242, 0.15)',
                border: '1px solid rgba(29, 161, 242, 0.3)',
                borderRadius: '8px',
                padding: '10px 8px',
                color: '#1DA1F2',
                textAlign: 'center',
                textDecoration: 'none',
                fontSize: '12px',
                fontWeight: 600,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '4px',
                transition: 'all 0.2s ease',
              }}
            >
              <span style={{ fontSize: '18px' }}>🐦</span>
              X (Twitter)
            </a>
            <a
              href={emailUrl}
              style={{
                background: 'rgba(232, 168, 56, 0.15)',
                border: '1px solid rgba(232, 168, 56, 0.3)',
                borderRadius: '8px',
                padding: '10px 8px',
                color: '#E8A838',
                textAlign: 'center',
                textDecoration: 'none',
                fontSize: '12px',
                fontWeight: 600,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '4px',
                transition: 'all 0.2s ease',
              }}
            >
              <span style={{ fontSize: '18px' }}>✉️</span>
              Email
            </a>
          </div>
        </div>

        {/* Export & Download Options */}
        <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)', paddingTop: '14px', display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'center' }}>
          {onDownloadPdf && (
            <button
              onClick={onDownloadPdf}
              disabled={isDownloadingPdf}
              style={{
                width: '100%',
                background: 'rgba(255, 255, 255, 0.08)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '8px',
                padding: '8px 16px',
                color: '#ffffff',
                fontSize: '13px',
                fontWeight: 600,
                cursor: isDownloadingPdf ? 'wait' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                transition: 'all 0.2s ease',
              }}
            >
              {isDownloadingPdf ? '⏳ Generating PDF Brochure...' : '📄 Download Printable PDF Brochure'}
            </button>
          )}

          <button
            onClick={() => {
              const url = `http://localhost:8000/export/ical/${itinerary.id}`;
              const a = document.createElement('a');
              a.href = url;
              a.download = `WanderAI-${dest}.ics`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
            }}
            style={{
              width: '100%',
              background: 'rgba(0, 219, 231, 0.1)',
              border: '1px solid rgba(0, 219, 231, 0.3)',
              borderRadius: '8px',
              padding: '8px 16px',
              color: '#00DBE7',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              transition: 'all 0.2s ease',
            }}
          >
            📅 Export to Calendar (.ics / Google / Apple)
          </button>
        </div>
      </div>
    </div>
  );
}

