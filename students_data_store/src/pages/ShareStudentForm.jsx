import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/client';

export default function ShareStudentForm() {
  const { token } = useParams();
  const navigate = useNavigate();
  
  const [formConfig, setFormConfig] = useState(null);
  const [formData, setFormData] = useState({});
  const [loadingConfig, setLoadingConfig] = useState(true);
  
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const { data } = await api.get(`/forms/public/${token}`);
        setFormConfig(data);
        
        // Initialize form data state empty, React will handle the rest
        const initial = {};
        data.allowed_fields.forEach(f => {
          initial[f.name] = '';
        });
        setFormData(initial);
      } catch (err) {
        setError(err.response?.data?.detail || 'Invalid or deactivated form link.');
      } finally {
        setLoadingConfig(false);
      }
    };
    
    if (token) fetchConfig();
  }, [token]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.post(`/forms/public/${token}/submit`, formData);
      setSubmitted(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit form. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const inputClass = "w-full border border-gray-300 rounded-lg px-3.5 py-2.5 text-sm text-gray-900 outline-none transition-all focus:border-indigo-500 focus:ring-[3px] focus:ring-indigo-500/10 placeholder:text-gray-400 bg-white";
  const labelClass = "block text-[0.8125rem] font-medium text-gray-700 mb-1.5";

  if (loadingConfig) {
    return <div className="min-h-screen flex items-center justify-center bg-gray-50">Loading form...</div>;
  }

  if (error && !formConfig) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="bg-white p-8 rounded-2xl shadow-sm text-center max-w-sm">
          <div className="text-4xl mb-4">🚫</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Unavailable</h2>
          <p className="text-gray-500 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 font-sans p-4">
        <div className="bg-white border border-gray-200 rounded-xl p-10 w-full max-w-[500px] shadow-sm text-center">
          <div className="text-4xl mb-3">✅</div>
          <h1 className="text-xl font-bold text-gray-900 mb-1">Thank You!</h1>
          <p className="text-sm text-gray-500 mb-6">We have received your details and will review them shortly.</p>
          <button
            onClick={() => window.location.reload()}
            className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition-colors text-sm"
          >
            Submit Another Reference
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 font-sans p-4 py-12">
      <div className="bg-white border border-gray-200 rounded-xl p-10 w-full max-w-[600px] shadow-sm">
        <div className="text-center mb-8">
          <div className="text-4xl mb-3">📝</div>
          <h1 className="text-xl font-bold text-gray-900 mb-1">{formConfig.title}</h1>
          <p className="text-sm text-gray-500">Please provide your details below.</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4.5 space-y-4">
          {error && <div className="bg-red-50 border border-red-200 text-red-700 px-3.5 py-2.5 rounded-lg text-[0.8125rem] mb-2">{error}</div>}

          {formConfig.allowed_fields.map((field) => (
            <div key={field.name}>
              <label htmlFor={field.name} className={labelClass}>
                {field.label} {field.required && '*'}
              </label>
              <input 
                id={field.name} 
                name={field.name} 
                type={field.type === 'date' ? 'date' : field.name === 'email' ? 'email' : 'text'} 
                required={field.required}
                value={formData[field.name] || ''} 
                onChange={handleChange} 
                className={inputClass} 
              />
            </div>
          ))}

          <button type="submit" disabled={loading} className="w-full py-3 mt-4 bg-indigo-600 border-none rounded-lg text-white text-sm font-semibold cursor-pointer transition-all flex items-center justify-center gap-2 hover:bg-indigo-700 disabled:opacity-60">
            {loading ? <span className="w-4 h-4 border-2 border-white/35 border-t-white rounded-full animate-spin" /> : '📤 Submit Application'}
          </button>
        </form>
      </div>
    </div>
  );
}
