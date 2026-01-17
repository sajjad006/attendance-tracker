import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import {
  User,
  Calendar,
  Plus,
  Edit2,
  Trash2,
  Check,
  Lock,
} from 'lucide-react';
import { Card, Button, Input, Modal, Badge, LoadingSpinner } from '../components/ui';
import { authApi } from '../api/auth';
import { semesterApi } from '../api/academic';
import { useAuth } from '../context/AuthContext';
import { useSemester } from '../context/SemesterContext';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile');

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'semesters', label: 'Semesters', icon: Calendar },
    { id: 'password', label: 'Password', icon: Lock },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Manage your account and preferences</p>
      </div>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Sidebar */}
        <Card className="p-4 md:w-64 shrink-0">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                  activeTab === tab.id
                    ? 'bg-indigo-50 text-indigo-600'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <tab.icon
                  className={`h-5 w-5 mr-3 ${
                    activeTab === tab.id ? 'text-indigo-600' : 'text-gray-400'
                  }`}
                />
                {tab.label}
              </button>
            ))}
          </nav>
        </Card>

        {/* Content */}
        <div className="flex-1">
          {activeTab === 'profile' && <ProfileSection />}
          {activeTab === 'semesters' && <SemestersSection />}
          {activeTab === 'password' && <PasswordSection />}
        </div>
      </div>
    </div>
  );
}

function ProfileSection() {
  const { user, updateUser } = useAuth();
  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    timezone: user?.timezone || 'UTC',
  });
  const [message, setMessage] = useState('');

  const mutation = useMutation({
    mutationFn: authApi.updateProfile,
    onSuccess: (data) => {
      updateUser(data.user || data);
      setMessage('Profile updated successfully');
      setTimeout(() => setMessage(''), 3000);
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  return (
    <Card className="p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Profile Information</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        {message && (
          <div className="p-3 bg-green-50 border border-green-200 text-green-700 text-sm rounded-lg">
            {message}
          </div>
        )}

        <Input
          label="Username"
          value={formData.username}
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          disabled
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="First Name"
            value={formData.first_name}
            onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
          />
          <Input
            label="Last Name"
            value={formData.last_name}
            onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
          />
        </div>

        <Input
          label="Email"
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        />

        <Button type="submit" loading={mutation.isPending}>
          Save Changes
        </Button>
      </form>
    </Card>
  );
}

function SemestersSection() {
  const [showModal, setShowModal] = useState(false);
  const [editingSemester, setEditingSemester] = useState(null);
  const { refetch: refetchSemesterContext } = useSemester();
  const queryClient = useQueryClient();

  const { data: semesters = [], isLoading } = useQuery({
    queryKey: ['semesters'],
    queryFn: semesterApi.getAll,
  });

  const deleteMutation = useMutation({
    mutationFn: semesterApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['semesters']);
      refetchSemesterContext();
    },
  });

  const setCurrentMutation = useMutation({
    mutationFn: semesterApi.setAsCurrent,
    onSuccess: () => {
      queryClient.invalidateQueries(['semesters']);
      refetchSemesterContext();
    },
  });

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Semesters</h2>
        <Button onClick={() => setShowModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Semester
        </Button>
      </div>

      <div className="space-y-3">
        {semesters.map((semester) => (
          <div
            key={semester.id}
            className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
          >
            <div>
              <div className="flex items-center gap-2">
                <p className="font-medium text-gray-900">{semester.name}</p>
                {semester.is_current && (
                  <Badge variant="success">Current</Badge>
                )}
                <Badge
                  variant={
                    semester.status === 'active'
                      ? 'info'
                      : semester.status === 'completed'
                      ? 'default'
                      : 'warning'
                  }
                >
                  {semester.status}
                </Badge>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {format(new Date(semester.start_date), 'MMM d, yyyy')} -{' '}
                {format(new Date(semester.end_date), 'MMM d, yyyy')}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {!semester.is_current && (
                <button
                  onClick={() => setCurrentMutation.mutate(semester.id)}
                  className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg"
                  title="Set as Current"
                >
                  <Check className="h-4 w-4" />
                </button>
              )}
              <button
                onClick={() => setEditingSemester(semester)}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded-lg"
              >
                <Edit2 className="h-4 w-4" />
              </button>
              <button
                onClick={() => {
                  if (confirm('Are you sure? This will delete all associated data.')) {
                    deleteMutation.mutate(semester.id);
                  }
                }}
                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}

        {semesters.length === 0 && (
          <p className="text-gray-500 text-center py-8">
            No semesters yet. Create one to get started.
          </p>
        )}
      </div>

      <SemesterModal
        isOpen={showModal || !!editingSemester}
        onClose={() => {
          setShowModal(false);
          setEditingSemester(null);
        }}
        semester={editingSemester}
      />
    </Card>
  );
}

function SemesterModal({ isOpen, onClose, semester }) {
  const [formData, setFormData] = useState({
    name: semester?.name || '',
    start_date: semester?.start_date || format(new Date(), 'yyyy-MM-dd'),
    end_date: semester?.end_date || '',
    status: semester?.status || 'active',
    is_current: semester?.is_current || false,
  });
  const queryClient = useQueryClient();
  const { refetch } = useSemester();

  const mutation = useMutation({
    mutationFn: semester
      ? (data) => semesterApi.update(semester.id, data)
      : semesterApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['semesters']);
      refetch();
      onClose();
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={semester ? 'Edit Semester' : 'Create Semester'}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Semester Name"
          required
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="e.g., Fall 2024"
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Start Date"
            type="date"
            required
            value={formData.start_date}
            onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
          />
          <Input
            label="End Date"
            type="date"
            required
            value={formData.end_date}
            onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
          />
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="is_current"
            checked={formData.is_current}
            onChange={(e) => setFormData({ ...formData, is_current: e.target.checked })}
            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
          />
          <label htmlFor="is_current" className="text-sm text-gray-700">
            Set as current semester
          </label>
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending}>
            {semester ? 'Save Changes' : 'Create Semester'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function PasswordSection() {
  const [formData, setFormData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [message, setMessage] = useState({ type: '', text: '' });

  const mutation = useMutation({
    mutationFn: authApi.changePassword,
    onSuccess: () => {
      setMessage({ type: 'success', text: 'Password changed successfully' });
      setFormData({ current_password: '', new_password: '', confirm_password: '' });
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    },
    onError: (error) => {
      setMessage({
        type: 'error',
        text: error.response?.data?.error || 'Failed to change password',
      });
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (formData.new_password !== formData.confirm_password) {
      setMessage({ type: 'error', text: 'New passwords do not match' });
      return;
    }
    mutation.mutate({
      current_password: formData.current_password,
      new_password: formData.new_password,
    });
  };

  return (
    <Card className="p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Change Password</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        {message.text && (
          <div
            className={`p-3 border text-sm rounded-lg ${
              message.type === 'success'
                ? 'bg-green-50 border-green-200 text-green-700'
                : 'bg-red-50 border-red-200 text-red-700'
            }`}
          >
            {message.text}
          </div>
        )}

        <Input
          label="Current Password"
          type="password"
          required
          value={formData.current_password}
          onChange={(e) =>
            setFormData({ ...formData, current_password: e.target.value })
          }
        />

        <Input
          label="New Password"
          type="password"
          required
          value={formData.new_password}
          onChange={(e) =>
            setFormData({ ...formData, new_password: e.target.value })
          }
        />

        <Input
          label="Confirm New Password"
          type="password"
          required
          value={formData.confirm_password}
          onChange={(e) =>
            setFormData({ ...formData, confirm_password: e.target.value })
          }
        />

        <Button type="submit" loading={mutation.isPending}>
          Change Password
        </Button>
      </form>
    </Card>
  );
}
