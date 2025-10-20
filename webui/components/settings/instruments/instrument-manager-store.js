/**
 * Instrument Manager Store
 * Manages state and operations for the instrument manager modal
 */

import { createStore } from "/js/AlpineStore.js";

const model = {
    instruments: [],
    loading: false,
    error: null,
    filterProfile: '',
    filterType: '',
    filterEnabled: '',

    async initialize() {
        await this.loadInstruments();
    },

        async loadInstruments() {
            this.loading = true;
            this.error = null;

            try {
                // Build query parameters
                const params = new URLSearchParams();
                if (this.filterProfile) params.append('profile', this.filterProfile);
                if (this.filterType) params.append('type', this.filterType);
                if (this.filterEnabled) params.append('enabled', this.filterEnabled);

                const queryString = params.toString();
                const url = `/api/instrument_list${queryString ? '?' + queryString : ''}`;

                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        profile: this.filterProfile,
                        type: this.filterType,
                        enabled: this.filterEnabled,
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.success) {
                    this.instruments = data.instruments || [];
                } else {
                    throw new Error(data.error || 'Failed to load instruments');
                }
            } catch (error) {
                console.error('Error loading instruments:', error);
                this.error = error.message;
                this.instruments = [];
            } finally {
                this.loading = false;
            }
        },

        async toggleEnabled(instrument) {
            const newEnabledState = !instrument.enabled;

            try {
                const response = await fetch('/api/instrument_update', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': localStorage.getItem('a0_api_key') || '',
                    },
                    body: JSON.stringify({
                        instrument_id: instrument.id,
                        enabled: newEnabledState,
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.success) {
                    // Update local state
                    instrument.enabled = newEnabledState;
                    
                    // Show success feedback
                    this.showNotification(`Instrument ${newEnabledState ? 'enabled' : 'disabled'} successfully`);
                } else {
                    throw new Error(data.error || 'Failed to update instrument');
                }
            } catch (error) {
                console.error('Error toggling instrument:', error);
                this.error = error.message;
                
                // Reload to restore correct state
                await this.loadInstruments();
            }
        },

        editInstrument(instrument) {
            // For now, show a simple prompt-based editor
            // In a full implementation, this would open a detailed modal
            const newProfiles = prompt(
                `Edit profiles for ${instrument.display_name || instrument.id}\nEnter comma-separated profile names:`,
                (instrument.profiles || ['default']).join(', ')
            );

            if (newProfiles === null) return; // User cancelled

            const newTags = prompt(
                `Edit tags for ${instrument.display_name || instrument.id}\nEnter comma-separated tags:`,
                (instrument.tags || []).join(', ')
            );

            if (newTags === null) return; // User cancelled

            const newPriority = prompt(
                `Edit priority for ${instrument.display_name || instrument.id}\nEnter priority (1-100):`,
                instrument.priority || 5
            );

            if (newPriority === null) return; // User cancelled

            this.updateInstrument(instrument.id, {
                profiles: newProfiles.split(',').map(p => p.trim()).filter(p => p),
                tags: newTags.split(',').map(t => t.trim()).filter(t => t),
                priority: parseInt(newPriority) || 5,
            });
        },

        async updateInstrument(instrumentId, updates) {
            try {
                const response = await fetch('/api/instrument_update', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': localStorage.getItem('a0_api_key') || '',
                    },
                    body: JSON.stringify({
                        instrument_id: instrumentId,
                        ...updates,
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.success) {
                    this.showNotification('Instrument updated successfully');
                    await this.loadInstruments();
                } else {
                    throw new Error(data.error || 'Failed to update instrument');
                }
            } catch (error) {
                console.error('Error updating instrument:', error);
                this.error = error.message;
            }
        },

        showNotification(message) {
            // Simple notification - in production, use a proper notification system
            console.log('Notification:', message);
            
            // Create a temporary notification element
            const notification = document.createElement('div');
            notification.textContent = message;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                background: #2a4a2a;
                color: #8f8;
                border: 1px solid #4a4;
                border-radius: 4px;
                z-index: 10000;
                animation: slideIn 0.3s ease-out;
            `;
            document.body.appendChild(notification);

            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease-in';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        },

    closeModal() {
        if (typeof closeModal === 'function') {
            closeModal();
        }
    },

    onClose() {
        // Cleanup when modal closes
    }
};

// Add notification animations
if (!document.getElementById('notification-animations')) {
    const style = document.createElement('style');
    style.id = 'notification-animations';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

export const store = createStore("instrumentManagerStore", model);

