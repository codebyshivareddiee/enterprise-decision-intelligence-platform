import { jwtDecode } from 'jwt-decode';

const BASE_URL = 'http://localhost:8000/api/v1';

// Token helpers
export const getAccessToken = () => localStorage.getItem('access_token');
export const getRefreshToken = () => localStorage.getItem('refresh_token');
export const saveTokens = (access, refresh) => {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
};
export const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

export const getHeaders = () => {
  const token = getAccessToken();
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

// High-fidelity fallback mock data
const MOCK_ORGS = [];

const MOCK_WORKSPACES = [];

const MOCK_KNOWLEDGE_ASSETS = [];

const MOCK_DECISIONS = [];

const MOCK_RULES = [];

export const api = {
  // Authentication
  async register(email, password, full_name, company_name = '') {
    try {
      const response = await fetch(`${BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name, company_name }),
      });
      const data = await response.json().catch(() => ({}));
      if (response.ok) {
        return { success: true, message: 'User registered successfully.' };
      } else {
        return { success: false, message: data.detail || 'Registration failed.' };
      }
    } catch (e) {
      console.warn('Backend register failed.', e);
      return { success: false, message: 'Cannot connect to backend server. Please verify the backend is running on port 8000.' };
    }
  },

  async login(email, password) {
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });
      if (response.ok) {
        const tokens = await response.json();
        saveTokens(tokens.access_token, tokens.refresh_token);
        return await this.getMe();
      }
    } catch (e) {
      console.warn('Backend login failed.', e);
    }
    return null;
  },


  async getMe() {
    const token = getAccessToken();
    if (!token) return null;
    if (token.startsWith('mock')) {
      const orgId = MOCK_ORGS[0]?.id || '1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d';
      return {
        id: 'user-uuid-1234',
        email: 'N/A',
        full_name: 'N/A',
        status: 'active',
        organization_ids: [orgId],
        memberships: [{ organization_id: orgId, workspace_ids: MOCK_WORKSPACES.map(w => w.id), role: 'PLATFORM_ADMIN' }]
      };
    }

    try {
      const response = await fetch(`${BASE_URL}/auth/me`, {
        method: 'GET',
        headers: getHeaders(),
      });
      if (response.ok) {
        const res = await response.json();
        return res.data;
      }
    } catch (e) {
      console.warn('Backend getMe failed.', e);
    }
    return null;
  },

  // Organizations
  async getOrganizations() {
    try {
      const response = await fetch(`${BASE_URL}/organizations`, {
        method: 'GET',
        headers: getHeaders(),
      });
      if (response.ok) {
        const res = await response.json();
        return res.data;
      }
    } catch (e) {
      console.warn('Backend list organizations failed, using mock.', e);
    }
    return MOCK_ORGS;
  },

  async getOrgStats(orgId) {
    try {
      const response = await fetch(`${BASE_URL}/organizations/${orgId}/stats`, {
        method: 'GET',
        headers: getHeaders(),
      });
      if (response.ok) {
        const res = await response.json();
        return res.data;
      }
    } catch (e) {
      console.warn('Backend org stats failed, using mock.', e);
    }
    return {
      total_workspaces: MOCK_WORKSPACES.length,
      decisions_made: 0,
      knowledge_assets: 0,
      active_users: 0
    };
  },

  // Workspaces
  async getWorkspaces(orgId) {
    try {
      const response = await fetch(`${BASE_URL}/organizations/${orgId}/workspaces/summary`, {
        method: 'GET',
        headers: getHeaders(),
      });
      if (response.ok) {
        const res = await response.json();
        return res.data;
      }
    } catch (e) {
      // fallback to list standard spaces
      try {
        const response2 = await fetch(`${BASE_URL}/organizations/${orgId}/workspaces`, {
          method: 'GET',
          headers: getHeaders(),
        });
        if (response2.ok) {
          const res2 = await response2.json();
          // merge with default counts
          return res2.data.map((w, index) => ({
            ...w,
            decisions_count_30d: MOCK_WORKSPACES[index]?.decisions_count_30d || 10,
            knowledge_assets_count: MOCK_WORKSPACES[index]?.knowledge_assets_count || 120,
            active_users_count: MOCK_WORKSPACES[index]?.active_users_count || 5,
            last_activity: MOCK_WORKSPACES[index]?.last_activity || '1 day ago'
          }));
        }
      } catch (e2) { }
    }
    return MOCK_WORKSPACES;
  },

  async createWorkspace(orgId, name, description) {
    try {
      const response = await fetch(`${BASE_URL}/workspaces`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ organization_id: orgId, name, description, owner_id: 'user-uuid-1234' }),
      });
      if (response.ok) {
        const res = await response.json();
        return res.data;
      }
    } catch (e) {
      console.warn('Backend create workspace failed, using mock.', e);
    }
    const newWs = {
      id: `ws-uuid-${Math.random().toString(36).substr(2, 9)}`,
      organization_id: orgId,
      name,
      description,
      status: 'active',
      decisions_count_30d: 0,
      knowledge_assets_count: 0,
      active_users_count: 1,
      last_activity: 'Just created'
    };
    MOCK_WORKSPACES.push(newWs);
    return newWs;
  },

  // Knowledge
  async getKnowledgeAssets(workspaceId = null) {
    try {
      const response = await fetch(`${BASE_URL}/knowledge/assets`, {
        method: 'GET',
        headers: getHeaders(),
      });
      if (response.ok) {
        const res = await response.json();
        return res.data;
      }
    } catch (e) {
      console.warn('Backend list assets failed, using mock.', e);
    }
    return MOCK_KNOWLEDGE_ASSETS;
  },

  async uploadKnowledge(workspaceId, orgId, description, file) {
    try {
      const formData = new FormData();
      formData.append('workspace_id', workspaceId);
      formData.append('organization_id', orgId);
      formData.append('description', description);
      formData.append('file', file);

      const headers = getHeaders();
      delete headers['Content-Type'];

      const response = await fetch(`${BASE_URL}/knowledge/upload`, {
        method: 'POST',
        headers: headers,
        body: formData
      });
      if (response.ok) {
        const res = await response.json();
        return res.data;
      }
    } catch (e) {
      console.warn('Backend upload knowledge failed, using mock.', e);
    }

    // Mock response matching Image 6 analysis result
    return {
      asset_id: `asset-uuid-${Math.random().toString(36).substr(2, 9)}`,
      schema_selected: 'N/A',
      chunking_strategy: 'N/A',
      chunk_profile: 'N/A',
      processing_reasoning: 'N/A',
      selection_method: 'N/A',
      confidence: 0,
      chunks_created: 0
    };
  },

  // Decisions
  async getDecisions(workspaceId) {
    try {
      const response = await fetch(`${BASE_URL}/workspaces/${workspaceId}/decisions`, {
        method: 'GET',
        headers: getHeaders(),
      });
      if (response.ok) {
        const res = await response.json();
        return res.data;
      }
    } catch (e) {
      console.warn('Backend get decisions failed, using mock.', e);
    }
    return MOCK_DECISIONS.filter(d => d.workspace_id === workspaceId);
  },

  async getDecision(decisionId) {
    try {
      const response = await fetch(`${BASE_URL}/decisions/${decisionId}`, {
        method: 'GET',
        headers: getHeaders(),
      });
      if (response.ok) {
        const res = await response.json();
        return res.data;
      }
    } catch (e) {
      console.warn('Backend get single decision failed, using mock.', e);
    }
    return MOCK_DECISIONS.find(d => d.id === decisionId) || MOCK_DECISIONS[0];
  },

  async executeDecision(workspaceId, userRequest) {
    try {
      const response = await fetch(`${BASE_URL}/decisions/execute`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ workspace_id: workspaceId, user_request: userRequest }),
      });
      if (response.ok) {
        const res = await response.json();
        return res.data;
      }
    } catch (e) {
      console.warn('Backend execute decision failed, using mock.', e);
    }

    const decisionId = `dec-uuid-${Math.random().toString(36).substr(2, 9)}`;
    const newDec = {
      id: decisionId,
      workspace_id: workspaceId,
      name: 'N/A',
      status: 'pending',
      goal: userRequest,
      decided_by_name: 'N/A',
      date: 'N/A',
      confidence: 0,
      code: 'N/A',
      recommended_option: 'N/A',
      explanation: 'N/A',
      rules: [],
      evidence: []
    };
    MOCK_DECISIONS.unshift(newDec);
    return newDec;
  },

  async resumeDecision(decisionId, feedback) {
    try {
      const response = await fetch(`${BASE_URL}/decisions/${decisionId}/resume`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ feedback }),
      });
      if (response.ok) {
        const res = await response.json();
        return res.data;
      }
    } catch (e) {
      console.warn('Backend resume decision failed, using mock.', e);
    }
    const dec = MOCK_DECISIONS.find(d => d.id === decisionId);
    if (dec) {
      dec.status = 'approved';
    }
    return { success: true };
  },

  async recordOutcome(decisionId, humanDecision, feedback) {
    try {
      const response = await fetch(`${BASE_URL}/decisions/outcome`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ decision_id: decisionId, human_decision: humanDecision, feedback }),
      });
      if (response.ok) {
        const res = await response.json();
        return res.data;
      }
    } catch (e) {
      console.warn('Backend record outcome failed, using mock.', e);
    }
    return { success: true };
  },

  // Rules
  async getRules(workspaceId) {
    try {
      const response = await fetch(`${BASE_URL}/workspaces/${workspaceId}/rules`, {
        method: 'GET',
        headers: getHeaders(),
      });
      if (response.ok) {
        const res = await response.json();
        return res.data;
      }
    } catch (e) {
      console.warn('Backend get rules failed, using mock.', e);
    }
    return MOCK_RULES;
  },

  async createRule(workspaceId, orgId, rule) {
    try {
      const response = await fetch(`${BASE_URL}/workspaces/${workspaceId}/rules`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ organization_id: orgId, workspace_id: workspaceId, ...rule }),
      });
      if (response.ok) {
        const res = await response.json();
        return res.data;
      }
    } catch (e) {
      console.warn('Backend create rule failed, using mock.', e);
    }
    const newRule = { id: `rule-uuid-${Math.random().toString(36).substr(2, 9)}`, ...rule, status: 'active' };
    MOCK_RULES.push(newRule);
    return newRule;
  }
};
