import React, { useState } from 'react';
import {
  BarChart3, Leaf, Zap, DollarSign, Boxes, Share2,
  TrendingDown, AlertCircle, CheckCircle2, Loader2,
  Info, ChevronDown, Gauge, PieChart, TrendingUp, Cpu
} from 'lucide-react';
import { API_BASE } from './config';

const DataCenterCalculator = ({ onToast }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    num_servers: 500,
    topology: 'spine_leaf',
    annual_power_kwh: 1000000,
    baseline_pue: 1.67,
    optimized_pue: 1.1,
    region: 'EU'
  });

  const [roiData, setRoiData] = useState({
    investment_eur: 500000,
    annual_savings_eur: 100000
  });

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleRoiChange = (field, value) => {
    setRoiData(prev => ({ ...prev, [field]: value }));
  };

  const runComprehensiveAnalysis = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/calculator/comprehensive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setResults(data.data);
      setActiveTab('results');
      onToast('Analysis complete!', 'success');
    } catch (e) {
      onToast(`Analysis failed: ${e.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const runROIAnalysis = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/calculator/roi-analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          num_servers: formData.num_servers,
          ...roiData
        })
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setResults({ roi: data.data });
      setActiveTab('roi');
      onToast('ROI Analysis complete!', 'success');
    } catch (e) {
      onToast(`ROI Analysis failed: ${e.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="calculator-container">
      <div className="card">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          marginBottom: '2rem',
          paddingBottom: '1.5rem',
          borderBottom: '1px solid var(--border)'
        }}>
          <Boxes size={32} color="var(--accent-green)" />
          <div>
            <h2 style={{ fontSize: '1.8rem', marginalTom: '0', marginBottom: '0.25rem' }}>
              Data Center Calculator
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Comprehensive sustainability & ROI analysis
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          marginBottom: '2rem',
          borderBottom: '1px solid var(--border)',
          paddingBottom: '1rem'
        }}>
          {['overview', 'parameters', 'roi', 'results'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '0.75rem 1.5rem',
                background: activeTab === tab ? 'var(--accent-green)' : 'transparent',
                color: activeTab === tab ? 'white' : 'var(--text-secondary)',
                border: 'none',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: activeTab === tab ? '600' : '400',
                transition: 'all 0.3s ease'
              }}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '1.5rem',
              marginBottom: '2rem'
            }}>
              <div style={{
                padding: '1.5rem',
                background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05))',
                borderRadius: '0.75rem',
                borderLeft: '4px solid var(--accent-green)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <Leaf size={18} color="var(--accent-green)" />
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Embodied Carbon</span>
                </div>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  Calculate emissions from hardware manufacturing
                </p>
              </div>

              <div style={{
                padding: '1.5rem',
                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.05))',
                borderRadius: '0.75rem',
                borderLeft: '4px solid var(--accent-blue)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <Share2 size={18} color="var(--accent-blue)" />
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Network Topology</span>
                </div>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  Analyze architecture requirements and footprint
                </p>
              </div>

              <div style={{
                padding: '1.5rem',
                background: 'linear-gradient(135deg, rgba(249, 115, 22, 0.1), rgba(249, 115, 22, 0.05))',
                borderRadius: '0.75rem',
                borderLeft: '4px solid var(--accent-orange)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <Zap size={18} color="var(--accent-orange)" />
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Operational Carbon</span>
                </div>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  Compare baseline vs. optimized scenarios
                </p>
              </div>

              <div style={{
                padding: '1.5rem',
                background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05))',
                borderRadius: '0.75rem',
                borderLeft: '4px solid var(--accent-green)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <DollarSign size={18} color="var(--accent-green)" />
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>ROI Analysis</span>
                </div>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  Financial return on investment projections
                </p>
              </div>
            </div>

            <div style={{
              padding: '1.5rem',
              background: 'rgba(59, 130, 246, 0.1)',
              borderRadius: '0.75rem',
              borderLeft: '4px solid var(--accent-blue)',
              display: 'flex',
              gap: '1rem'
            }}>
              <Info size={20} color="var(--accent-blue)" />
              <div>
                <p style={{ fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.25rem' }}>
                  Comprehensive Analysis
                </p>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  Run a full datacenter sustainability assessment combining operational, embodied, and network topology analysis.
                </p>
              </div>
            </div>

            <button
              onClick={runComprehensiveAnalysis}
              disabled={isLoading}
              style={{
                width: '100%',
                marginTop: '2rem',
                padding: '1rem',
                background: 'var(--accent-green)',
                color: 'white',
                border: 'none',
                borderRadius: '0.75rem',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.7 : 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                transition: 'all 0.3s ease'
              }}
            >
              {isLoading ? <Loader2 size={20} className="spin" /> : <BarChart3 size={20} />}
              {isLoading ? 'Analyzing...' : 'Run Analysis'}
            </button>
          </div>
        )}

        {/* Parameters Tab */}
        {activeTab === 'parameters' && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '1.5rem'
          }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                Number of Servers
              </label>
              <input
                type="number"
                value={formData.num_servers}
                onChange={(e) => handleInputChange('num_servers', parseInt(e.target.value))}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid var(--border)',
                  borderRadius: '0.5rem',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                Network Topology
              </label>
              <select
                value={formData.topology}
                onChange={(e) => handleInputChange('topology', e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid var(--border)',
                  borderRadius: '0.5rem',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem'
                }}
              >
                <option value="fat_tree">Fat-Tree</option>
                <option value="clos">Clos (3-Tier)</option>
                <option value="spine_leaf">Spine-Leaf</option>
                <option value="three_tier">Traditional (3-Tier)</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                Annual Power Consumption (kWh)
              </label>
              <input
                type="number"
                value={formData.annual_power_kwh}
                onChange={(e) => handleInputChange('annual_power_kwh', parseFloat(e.target.value))}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid var(--border)',
                  borderRadius: '0.5rem',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                Baseline PUE
              </label>
              <input
                type="number"
                step="0.1"
                value={formData.baseline_pue}
                onChange={(e) => handleInputChange('baseline_pue', parseFloat(e.target.value))}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid var(--border)',
                  borderRadius: '0.5rem',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                Optimized PUE (with SCARI)
              </label>
              <input
                type="number"
                step="0.1"
                value={formData.optimized_pue}
                onChange={(e) => handleInputChange('optimized_pue', parseFloat(e.target.value))}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid var(--border)',
                  borderRadius: '0.5rem',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                Region
              </label>
              <select
                value={formData.region}
                onChange={(e) => handleInputChange('region', e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid var(--border)',
                  borderRadius: '0.5rem',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem'
                }}
              >
                <option value="EU">Europe</option>
                <option value="US">USA</option>
                <option value="ASIA">Asia</option>
              </select>
            </div>
          </div>
        )}

        {/* ROI Tab */}
        {activeTab === 'roi' && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '1.5rem'
          }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                Investment Required (€)
              </label>
              <input
                type="number"
                value={roiData.investment_eur}
                onChange={(e) => handleRoiChange('investment_eur', parseFloat(e.target.value))}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid var(--border)',
                  borderRadius: '0.5rem',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                Annual Savings (€)
              </label>
              <input
                type="number"
                value={roiData.annual_savings_eur}
                onChange={(e) => handleRoiChange('annual_savings_eur', parseFloat(e.target.value))}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid var(--border)',
                  borderRadius: '0.5rem',
                  background: 'var(--bg-secondary)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9rem'
                }}
              />
            </div>

            <button
              onClick={runROIAnalysis}
              disabled={isLoading}
              style={{
                gridColumn: '1 / -1',
                padding: '1rem',
                background: 'var(--accent-green)',
                color: 'white',
                border: 'none',
                borderRadius: '0.75rem',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.7 : 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem'
              }}
            >
              {isLoading ? <Loader2 size={20} className="spin" /> : <DollarSign size={20} />}
              {isLoading ? 'Calculating...' : 'Calculate ROI'}
            </button>
          </div>
        )}

        {/* Results Tab */}
        {activeTab === 'results' && results && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {results.operational && (
              <div className="card">
                <div className="card-header">
                  <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '1.2rem' }}>
                    <TrendingDown size={20} color="var(--accent-success)" />
                    <span>Operational Carbon Footprint</span>
                  </h3>
                  <span className="badge badge-success">ENERGY</span>
                </div>
                
                {results.operational.improvements && (
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                    gap: '1rem',
                    padding: '1.5rem 0'
                  }}>
                    <div style={{
                      background: 'linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 212, 212, 0.05) 100%)',
                      border: '1px solid rgba(0, 255, 136, 0.2)',
                      borderRadius: '12px',
                      padding: '1.25rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.5rem'
                    }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                        CO₂ Reduction
                      </span>
                      <p style={{ fontSize: '2rem', fontWeight: 900, color: 'var(--accent-success)' }}>
                        {results.operational.improvements.co2_reduction_kg?.toLocaleString() || 'N/A'} <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>kg</span>
                      </p>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>per year</p>
                    </div>
                    
                    <div style={{
                      background: 'linear-gradient(135deg, rgba(3, 178, 109, 0.1) 0%, rgba(76, 175, 80, 0.05) 100%)',
                      border: '1px solid rgba(76, 175, 80, 0.2)',
                      borderRadius: '12px',
                      padding: '1.25rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.5rem'
                    }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                        Cost Savings
                      </span>
                      <p style={{ fontSize: '2rem', fontWeight: 900, color: '#4CAF50' }}>
                        €{results.operational.improvements.cost_savings_eur?.toLocaleString() || 'N/A'}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>annual ROI</p>
                    </div>
                    
                    <div style={{
                      background: 'linear-gradient(135deg, rgba(0, 172, 193, 0.1) 0%, rgba(0, 150, 136, 0.05) 100%)',
                      border: '1px solid rgba(0, 150, 136, 0.2)',
                      borderRadius: '12px',
                      padding: '1.25rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.5rem'
                    }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                        Break-Even Period
                      </span>
                      <p style={{ fontSize: '2rem', fontWeight: 900, color: 'var(--accent-teal)' }}>
                        {results.operational.improvements.breakeven_years === null ? '∞' : `${results.operational.improvements.breakeven_years}`}
                      </p>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>years</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {results.embodied && (
              <div className="card">
                <div className="card-header">
                  <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '1.2rem' }}>
                    <Leaf size={20} color="var(--accent-success)" />
                    <span>Embodied Carbon Analysis</span>
                  </h3>
                  <span className="badge badge-warning">MANUFACTURING</span>
                </div>
                
                <div style={{
                  background: 'linear-gradient(135deg, rgba(255, 170, 0, 0.1) 0%, rgba(255, 152, 0, 0.05) 100%)',
                  border: '1px solid rgba(255, 170, 0, 0.2)',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                  marginTop: '1.5rem'
                }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                    Total Manufacturing Emissions
                  </span>
                  <p style={{ fontSize: '2.5rem', fontWeight: 900, color: 'var(--accent-warning)' }}>
                    {results.embodied.total_embodied_co2_kg?.toLocaleString() || 'N/A'} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>kg CO₂</span>
                  </p>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                    One-time emissions from equipment manufacturing
                  </p>
                </div>
              </div>
            )}

            {results.roi && (
              <div className="card">
                <div className="card-header">
                  <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '1.2rem' }}>
                    <DollarSign size={20} color="var(--accent-success)" />
                    <span>Financial ROI Projection</span>
                  </h3>
                  <span className="badge badge-success">ECONOMICS</span>
                </div>
                
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  gap: '1.5rem',
                  marginTop: '1.5rem'
                }}>
                  <div style={{
                    background: 'linear-gradient(135deg, rgba(0, 255, 136, 0.1) 0%, rgba(0, 212, 212, 0.05) 100%)',
                    border: '1px solid rgba(0, 255, 136, 0.2)',
                    borderRadius: '12px',
                    padding: '1.5rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem'
                  }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                      Annual ROI
                    </span>
                    <p style={{ fontSize: '2.5rem', fontWeight: 900, color: 'var(--accent-success)' }}>
                      {results.roi.roi_percent_annual?.toLocaleString() || 'N/A'}%
                    </p>
                  </div>
                  
                  <div style={{
                    background: 'linear-gradient(135deg, rgba(0, 172, 193, 0.1) 0%, rgba(0, 150, 136, 0.05) 100%)',
                    border: '1px solid rgba(0, 150, 136, 0.2)',
                    borderRadius: '12px',
                    padding: '1.5rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem'
                  }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                      Payback Period
                    </span>
                    <p style={{ fontSize: '2.5rem', fontWeight: 900, color: 'var(--accent-teal)' }}>
                      {results.roi.payback_period_years === null ? '∞' : `${results.roi.payback_period_years}`}
                    </p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>years</p>
                  </div>
                  
                  <div style={{
                    background: 'linear-gradient(135deg, rgba(176, 36, 255, 0.1) 0%, rgba(156, 39, 176, 0.05) 100%)',
                    border: '1px solid rgba(176, 36, 255, 0.2)',
                    borderRadius: '12px',
                    padding: '1.5rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem'
                  }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                      10-Year Benefit
                    </span>
                    <p style={{ fontSize: '2.5rem', fontWeight: 900, color: 'var(--accent-purple)' }}>
                      €{results.roi.ten_year_net_benefit_eur?.toLocaleString() || 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <style jsx>{`
        .calculator-container {
          width: 100%;
        }

        .metric-card {
          padding: 1rem;
          background: var(--bg-secondary);
          border: 1px solid var(--border);
          border-radius: 0.75rem;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .spin {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default DataCenterCalculator;
