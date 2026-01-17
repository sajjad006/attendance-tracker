import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button, Input, Card } from '../components/ui';
import { Calendar } from 'lucide-react';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
    first_name: '',
    last_name: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({});

    if (formData.password !== formData.password_confirm) {
      setErrors({ password_confirm: 'Passwords do not match' });
      return;
    }

    setLoading(true);

    try {
      await register(formData);
      navigate('/');
    } catch (err) {
      if (err.response?.data) {
        setErrors(err.response.data);
      } else {
        setErrors({ general: 'Registration failed. Please try again.' });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-white py-12 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-indigo-100 rounded-xl">
              <Calendar className="h-10 w-10 text-indigo-600" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">AttendTrack</h1>
          <p className="mt-2 text-gray-600">Create your account</p>
        </div>

        <Card className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {errors.general && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
                {errors.general}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <Input
                label="First Name"
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                placeholder="John"
                error={errors.first_name}
              />
              <Input
                label="Last Name"
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                placeholder="Doe"
                error={errors.last_name}
              />
            </div>

            <Input
              label="Username"
              type="text"
              required
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              placeholder="johndoe"
              error={errors.username}
            />

            <Input
              label="Email (Optional)"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="john@example.com"
              error={errors.email}
            />

            <Input
              label="Password"
              type="password"
              required
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="••••••••"
              error={errors.password}
            />

            <Input
              label="Confirm Password"
              type="password"
              required
              value={formData.password_confirm}
              onChange={(e) => setFormData({ ...formData, password_confirm: e.target.value })}
              placeholder="••••••••"
              error={errors.password_confirm}
            />

            <Button type="submit" loading={loading} className="w-full">
              Create Account
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <Link to="/login" className="font-medium text-indigo-600 hover:text-indigo-500">
                Sign in
              </Link>
            </p>
          </div>
        </Card>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500 flex items-center justify-center gap-1 flex-wrap">
            <span>Made with</span>
            <span className="text-red-500">❤</span>
            <span>by</span>
            <span className="inline-flex items-end">
              {'JUMTC'.split('').map((letter, i) => (
                <span
                  key={i}
                  className={`inline-block ${i % 2 === 0 ? 'translate-y-1' : '-translate-y-1'} font-semibold text-indigo-600`}
                >
                  {letter}
                </span>
              ))} Outcast
            </span>
            <span className="text-xs text-gray-400 ml-1">(Sorry Placement Coordination Issue)</span>
          </p>
        </div>
      </div>
    </div>
  );
}
