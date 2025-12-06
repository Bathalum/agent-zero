const profileStore = {
    profiles: [],
    currentProfile: null,
    loading: false,
    error: null,

    async fetchProfiles() {
        this.loading = true;
        this.error = null;
        try {
            const response = await fetchApi('/api/profile_list', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            const data = await response.json();
            if (data.success) {
                this.profiles = data.profiles || [];
                const settingsResponse = await fetchApi('/api/settings_get', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
                const settings = await settingsResponse.json();
                // Try multiple paths; convert_out may return nested sections
                this.currentProfile = settings?.settings?.agent_profile
                    || settings?.settings?.agent?.agent_profile
                    || (Array.isArray(settings?.settings?.sections) ? (settings.settings.sections.find(s=>s.id==='agent')?.fields?.find(f=>f.id==='agent_profile')?.value) : null)
                    || null;
            } else {
                this.error = data.error || 'Failed to fetch profiles';
            }
        } catch (err) {
            this.error = err?.message || String(err);
        } finally {
            this.loading = false;
        }
    },

    async switchProfile(profileId) {
        this.loading = true;
        this.error = null;
        try {
            const response = await fetchApi('/api/profile_switch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_id: profileId })
            });
            const data = await response.json();
            if (data.success) {
                this.currentProfile = profileId;
                return true;
            } else {
                this.error = data.error || 'Failed to switch profile';
                return false;
            }
        } catch (err) {
            this.error = err?.message || String(err);
            return false;
        } finally {
            this.loading = false;
        }
    },

    async getProfileMetadata(profileId) {
        try {
            const response = await fetchApi('/api/profile_metadata_get', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_id: profileId })
            });
            const data = await response.json();
            return data.success ? data.metadata : null;
        } catch (err) {
            console.error('Failed to fetch profile metadata:', err);
            return null;
        }
    },

    async updateProfileMetadata(profileId, metadata) {
        try {
            const response = await fetchApi('/api/profile_metadata_set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_id: profileId, metadata })
            });
            const data = await response.json();
            if (data.success) {
                const idx = this.profiles.findIndex(p => p.id === profileId);
                if (idx >= 0) {
                    this.profiles[idx] = { ...this.profiles[idx], ...metadata };
                }
                return true;
            }
            return false;
        } catch (err) {
            console.error('Failed to update profile metadata:', err);
            return false;
        }
    },

    async getProfileInstruments(profileId) {
        try {
            const response = await fetchApi(`/api/profile_instruments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile: profileId, action: 'list' })
            });
            const data = await response.json();
            return data.success ? data.instruments : [];
        } catch (err) {
            console.error('Failed to fetch profile instruments:', err);
            return [];
        }
    },

    async assignInstrument(profileId, instrumentId) {
        try {
            const response = await fetchApi('/api/profile_instruments', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile: profileId, instrument_id: instrumentId, action: 'assign' })
            });
            const data = await response.json();
            return !!data.success;
        } catch (err) {
            console.error('Failed to assign instrument:', err);
            return false;
        }
    },

    async unassignInstrument(profileId, instrumentId) {
        try {
            const response = await fetchApi('/api/profile_instruments', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile: profileId, instrument_id: instrumentId, action: 'unassign' })
            });
            const data = await response.json();
            return !!data.success;
        } catch (err) {
            console.error('Failed to unassign instrument:', err);
            return false;
        }
    },

    // New advanced profile management APIs

    async createProfile(profileId, sourceId, metadata) {
        try {
            const response = await fetchApi('/api/profile_create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_id: profileId, source_id: sourceId, metadata })
            });
            const data = await response.json();
            if (data.success) {
                await this.fetchProfiles(); // Refresh list
            }
            return data;
        } catch (err) {
            console.error('Failed to create profile:', err);
            return { success: false, error: err?.message || String(err) };
        }
    },

    async deleteProfile(profileId) {
        try {
            const response = await fetchApi('/api/profile_delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_id: profileId })
            });
            const data = await response.json();
            if (data.success) {
                await this.fetchProfiles(); // Refresh list
            }
            return data;
        } catch (err) {
            console.error('Failed to delete profile:', err);
            return { success: false, error: err?.message || String(err) };
        }
    },

    async getPrompt(profileId, promptFile) {
        try {
            const response = await fetchApi('/api/profile_prompt_get', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_id: profileId, prompt_file: promptFile })
            });
            const data = await response.json();
            return data.success ? data.content : null;
        } catch (err) {
            console.error('Failed to get prompt:', err);
            return null;
        }
    },

    async setPrompt(profileId, promptFile, content) {
        try {
            const response = await fetchApi('/api/profile_prompt_set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_id: profileId, prompt_file: promptFile, content })
            });
            const data = await response.json();
            return data;
        } catch (err) {
            console.error('Failed to set prompt:', err);
            return { success: false, error: err?.message || String(err) };
        }
    },

    async getConfig(profileId) {
        try {
            const response = await fetchApi('/api/profile_config_get', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_id: profileId })
            });
            const data = await response.json();
            return data.success ? data.config : null;
        } catch (err) {
            console.error('Failed to get config:', err);
            return null;
        }
    },

    async setConfig(profileId, config) {
        try {
            const response = await fetchApi('/api/profile_config_set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_id: profileId, config })
            });
            const data = await response.json();
            return data;
        } catch (err) {
            console.error('Failed to set config:', err);
            return { success: false, error: err?.message || String(err) };
        }
    },

    async manageExtensions(profileId, action, extensionPath, content) {
        try {
            const body = { profile_id: profileId, action };
            if (extensionPath) body.extension_path = extensionPath;
            if (content) body.content = content;

            const response = await fetchApi('/api/profile_extensions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await response.json();
            return data;
        } catch (err) {
            console.error('Failed to manage extensions:', err);
            return { success: false, error: err?.message || String(err) };
        }
    },

    async manageTools(profileId, action, toolFile, content) {
        try {
            const body = { profile_id: profileId, action };
            if (toolFile) body.tool_file = toolFile;
            if (content) body.content = content;

            const response = await fetchApi('/api/profile_tools', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const data = await response.json();
            return data;
        } catch (err) {
            console.error('Failed to manage tools:', err);
            return { success: false, error: err?.message || String(err) };
        }
    },

    async validateProfile(profileId) {
        try {
            const response = await fetchApi('/api/profile_validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_id: profileId })
            });
            const data = await response.json();
            return data;
        } catch (err) {
            console.error('Failed to validate profile:', err);
            return { success: false, error: err?.message || String(err) };
        }
    },

    async exportProfile(profileId) {
        try {
            const response = await fetchApi('/api/profile_export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_id: profileId })
            });
            
            // Download the file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${profileId}_profile.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            return { success: true };
        } catch (err) {
            console.error('Failed to export profile:', err);
            return { success: false, error: err?.message || String(err) };
        }
    },

    async importProfile(profileId, zipData) {
        try {
            const response = await fetchApi('/api/profile_import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_id: profileId, zip_data: zipData })
            });
            const data = await response.json();
            if (data.success) {
                await this.fetchProfiles(); // Refresh list
            }
            return data;
        } catch (err) {
            console.error('Failed to import profile:', err);
            return { success: false, error: err?.message || String(err) };
        }
    }
};


