import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Plus,
  Edit2,
  Trash2,
  BookOpen,
  BarChart3,
} from 'lucide-react';
import { Card, Button, Badge, Modal, Input, EmptyState, LoadingSpinner } from '../components/ui';
import { subjectApi } from '../api/academic';
import { analyticsApi } from '../api/analytics';
import { useSemester } from '../context/SemesterContext';

export default function SubjectsPage() {
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingSubject, setEditingSubject] = useState(null);
  const { currentSemester } = useSemester();
  const queryClient = useQueryClient();

  const { data: subjects = [], isLoading } = useQuery({
    queryKey: ['subjects', currentSemester?.id],
    queryFn: () => subjectApi.getAll(currentSemester?.id),
    enabled: !!currentSemester,
  });

  const { data: analytics } = useQuery({
    queryKey: ['semester-analytics', currentSemester?.id],
    queryFn: () => analyticsApi.getSemesterAnalytics(currentSemester?.id),
    enabled: !!currentSemester,
  });

  const deleteMutation = useMutation({
    mutationFn: subjectApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['subjects']);
      queryClient.invalidateQueries(['dashboard']);
    },
  });

  const getSubjectStats = (subjectId) => {
    if (!analytics?.subjects) return null;
    return analytics.subjects.find((s) => s.subject_id === subjectId);
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Subjects</h1>
          <p className="text-gray-600 mt-1">
            Manage your subjects for {currentSemester?.name || 'this semester'}
          </p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Subject
        </Button>
      </div>

      {/* Subjects Grid */}
      {subjects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {subjects.map((subject) => {
            const stats = getSubjectStats(subject.id);
            const percentage = parseFloat(stats?.attendance_percentage) || 0;

            return (
              <Card key={subject.id} className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-gray-900">{subject.name}</h3>
                    {subject.code && (
                      <p className="text-sm text-gray-500">{subject.code}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setEditingSubject(subject)}
                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Are you sure you want to delete this subject?')) {
                          deleteMutation.mutate(subject.id);
                        }
                      }}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Stats */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Attendance</span>
                    <span
                      className={`font-medium ${
                        percentage >= 75
                          ? 'text-green-600'
                          : percentage >= 50
                          ? 'text-yellow-600'
                          : 'text-red-600'
                      }`}
                    >
                      {percentage}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        percentage >= 75
                          ? 'bg-green-500'
                          : percentage >= 50
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                      style={{ width: `${Math.min(percentage, 100)}%` }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-sm pt-2">
                    <span className="text-gray-600">
                      {stats?.total_attended || 0} / {stats?.total_conducted || 0} classes
                    </span>
                    <Badge
                      variant={
                        percentage >= 75
                          ? 'success'
                          : percentage >= 50
                          ? 'warning'
                          : 'danger'
                      }
                    >
                      {percentage >= 75 ? 'On Track' : percentage >= 50 ? 'At Risk' : 'Critical'}
                    </Badge>
                  </div>

                  <p className="text-xs text-gray-500">
                    {subject.credit ? `Credits: ${subject.credit} • ` : ''}Min Required: {subject.min_attendance_percentage || 75}%
                  </p>
                </div>

                {/* View Analytics Link */}
                <Link
                  to={`/analytics?subject=${subject.id}`}
                  className="mt-4 flex items-center justify-center gap-2 w-full py-2 text-sm text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 rounded-lg transition-colors"
                >
                  <BarChart3 className="h-4 w-4" />
                  View Analytics
                </Link>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card className="p-8">
          <EmptyState
            icon={BookOpen}
            title="No subjects yet"
            description="Add your first subject to start tracking attendance"
            action={
              <Button onClick={() => setShowAddModal(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Subject
              </Button>
            }
          />
        </Card>
      )}

      {/* Add/Edit Modal */}
      <SubjectModal
        isOpen={showAddModal || !!editingSubject}
        onClose={() => {
          setShowAddModal(false);
          setEditingSubject(null);
        }}
        subject={editingSubject}
        semesterId={currentSemester?.id}
      />
    </div>
  );
}

function SubjectModal({ isOpen, onClose, subject, semesterId }) {
  const [formData, setFormData] = useState({
    name: subject?.name || '',
    code: subject?.code || '',
    credit: subject?.credit || '',
    min_attendance_percentage: subject?.min_attendance_percentage || 75,
    semester: semesterId,
  });
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: subject
      ? (data) => subjectApi.update(subject.id, data)
      : subjectApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['subjects']);
      queryClient.invalidateQueries(['dashboard']);
      onClose();
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    const submitData = {
      ...formData,
      semester: semesterId,
      credit: formData.credit || 0,
    };
    mutation.mutate(submitData);
  };

  // Reset form when modal opens/closes or subject changes
  useEffect(() => {
    setFormData({
      name: subject?.name || '',
      code: subject?.code || '',
      credit: subject?.credit || '',
      min_attendance_percentage: subject?.min_attendance_percentage || 75,
      semester: semesterId,
    });
  }, [subject, semesterId, isOpen]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={subject ? 'Edit Subject' : 'Add Subject'}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Subject Name"
          required
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="e.g., Mathematics"
        />

        <Input
          label="Subject Code (Optional)"
          value={formData.code}
          onChange={(e) => setFormData({ ...formData, code: e.target.value })}
          placeholder="e.g., MATH101"
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Credits (Optional)"
            type="number"
            step="0.5"
            min="0"
            value={formData.credit}
            onChange={(e) => setFormData({ ...formData, credit: e.target.value })}
            placeholder="3"
          />
          <Input
            label="Min Attendance %"
            type="number"
            min="0"
            max="100"
            value={formData.min_attendance_percentage}
            onChange={(e) => setFormData({ ...formData, min_attendance_percentage: e.target.value })}
          />
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending}>
            {subject ? 'Save Changes' : 'Add Subject'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
