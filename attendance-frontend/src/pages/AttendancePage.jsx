import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  format,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  addMonths,
  subMonths,
  getDay,
} from 'date-fns';
import {
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  XCircle,
  MinusCircle,
  Plus,
  Calendar,
} from 'lucide-react';
import { Card, Button, Badge, Modal, Input, Select, LoadingSpinner } from '../components/ui';
import { attendanceApi } from '../api/attendance';
import { subjectApi } from '../api/academic';
import { useSemester } from '../context/SemesterContext';

export default function AttendancePage() {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const { currentSemester } = useSemester();
  const queryClient = useQueryClient();

  const { data: calendarData, isLoading } = useQuery({
    queryKey: ['calendar', currentSemester?.id, format(currentMonth, 'yyyy-MM')],
    queryFn: () =>
      attendanceApi.getCalendar(
        currentMonth.getFullYear(),
        currentMonth.getMonth() + 1,
        currentSemester?.id
      ),
    enabled: !!currentSemester,
  });

  const { data: subjects = [] } = useQuery({
    queryKey: ['subjects', currentSemester?.id],
    queryFn: () => subjectApi.getAll(currentSemester?.id),
    enabled: !!currentSemester,
  });

  const { data: dayRecords, refetch: refetchDayRecords } = useQuery({
    queryKey: ['day-attendance', selectedDate],
    queryFn: () =>
      attendanceApi.getAll({
        date: format(selectedDate, 'yyyy-MM-dd'),
        subject__semester: currentSemester?.id,
      }),
    enabled: !!selectedDate && !!currentSemester,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, status }) => attendanceApi.update(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries(['calendar']);
      queryClient.invalidateQueries(['day-attendance']);
      queryClient.invalidateQueries(['dashboard']);
    },
  });

  const generateMutation = useMutation({
    mutationFn: () => attendanceApi.generateForDate(currentSemester?.id, format(selectedDate, 'yyyy-MM-dd')),
    onSuccess: () => {
      queryClient.invalidateQueries(['calendar']);
      queryClient.invalidateQueries(['day-attendance']);
      refetchDayRecords();
    },
  });

  const daysInMonth = eachDayOfInterval({
    start: startOfMonth(currentMonth),
    end: endOfMonth(currentMonth),
  });

  const startDay = getDay(startOfMonth(currentMonth));
  const emptyDays = Array(startDay).fill(null);

  const getDayStats = (date) => {
    if (!calendarData?.days) return null;
    const dateStr = format(date, 'yyyy-MM-dd');
    return calendarData.days[dateStr];
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'present':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'absent':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled':
        return <MinusCircle className="h-4 w-4 text-yellow-500" />;
      default:
        return null;
    }
  };

  const handleStatusChange = (recordId, newStatus) => {
    updateMutation.mutate({ id: recordId, status: newStatus });
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Attendance</h1>
          <p className="text-gray-600 mt-1">Track and manage your class attendance</p>
        </div>
        <Button onClick={() => setShowAddModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Extra Class
        </Button>
      </div>

      {/* Calendar */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <h2 className="text-lg font-semibold text-gray-900">
            {format(currentMonth, 'MMMM yyyy')}
          </h2>
          <button
            onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>

        {/* Day headers */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
            <div key={day} className="text-center text-sm font-medium text-gray-500 py-2">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar grid */}
        <div className="grid grid-cols-7 gap-1">
          {emptyDays.map((_, index) => (
            <div key={`empty-${index}`} className="aspect-square" />
          ))}
          {daysInMonth.map((day) => {
            const stats = getDayStats(day);
            const isToday = isSameDay(day, new Date());
            const isSelected = selectedDate && isSameDay(day, selectedDate);
            const hasClasses = stats && stats.total > 0;

            return (
              <button
                key={day.toISOString()}
                onClick={() => setSelectedDate(day)}
                className={`aspect-square p-1 rounded-lg border transition-colors ${
                  isSelected
                    ? 'border-indigo-500 bg-indigo-50'
                    : isToday
                    ? 'border-indigo-300 bg-indigo-50'
                    : hasClasses
                    ? 'border-gray-200 hover:border-gray-300'
                    : 'border-transparent hover:bg-gray-50'
                }`}
              >
                <div className="h-full flex flex-col items-center justify-center">
                  <span
                    className={`text-sm ${
                      isToday ? 'font-bold text-indigo-600' : 'text-gray-900'
                    }`}
                  >
                    {format(day, 'd')}
                  </span>
                  {hasClasses && (
                    <div className="flex items-center gap-0.5 mt-1">
                      {stats.present > 0 && (
                        <div className="w-2 h-2 bg-green-500 rounded-full" />
                      )}
                      {stats.absent > 0 && (
                        <div className="w-2 h-2 bg-red-500 rounded-full" />
                      )}
                      {stats.cancelled > 0 && (
                        <div className="w-2 h-2 bg-yellow-500 rounded-full" />
                      )}
                    </div>
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full" />
            <span className="text-sm text-gray-600">Present</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded-full" />
            <span className="text-sm text-gray-600">Absent</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full" />
            <span className="text-sm text-gray-600">Cancelled</span>
          </div>
        </div>
      </Card>

      {/* Selected Day Details */}
      {selectedDate && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Classes on {format(selectedDate, 'EEEE, MMMM d, yyyy')}
          </h3>
          {dayRecords?.length > 0 ? (
            <div className="space-y-3">
              {dayRecords.map((record) => (
                <div
                  key={record.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    {getStatusIcon(record.status)}
                    <div>
                      <p className="font-medium text-gray-900">{record.subject_name}</p>
                      <p className="text-sm text-gray-500">
                        {record.start_time} - {record.end_time}
                        {record.attendance_type === 'adhoc' && (
                          <Badge variant="info" className="ml-2">Extra Class</Badge>
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleStatusChange(record.id, 'present')}
                      className={`p-2 rounded-lg transition-colors ${
                        record.status === 'present'
                          ? 'bg-green-100 text-green-600'
                          : 'hover:bg-gray-200 text-gray-400'
                      }`}
                      title="Mark Present"
                    >
                      <CheckCircle className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleStatusChange(record.id, 'absent')}
                      className={`p-2 rounded-lg transition-colors ${
                        record.status === 'absent'
                          ? 'bg-red-100 text-red-600'
                          : 'hover:bg-gray-200 text-gray-400'
                      }`}
                      title="Mark Absent"
                    >
                      <XCircle className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleStatusChange(record.id, 'cancelled')}
                      className={`p-2 rounded-lg transition-colors ${
                        record.status === 'cancelled'
                          ? 'bg-yellow-100 text-yellow-600'
                          : 'hover:bg-gray-200 text-gray-400'
                      }`}
                      title="Mark Cancelled"
                    >
                      <MinusCircle className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">No classes scheduled for this day</p>
              <div className="flex justify-center gap-3">
                <Button
                  onClick={() => generateMutation.mutate()}
                  loading={generateMutation.isPending}
                  variant="outline"
                >
                  <Calendar className="h-4 w-4 mr-2" />
                  Generate from Routine
                </Button>
                <Button onClick={() => setShowAddModal(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Extra Class
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Add Extra Class Modal */}
      <AddExtraClassModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        subjects={subjects}
        semesterId={currentSemester?.id}
      />
    </div>
  );
}

function AddExtraClassModal({ isOpen, onClose, subjects, semesterId }) {
  const [formData, setFormData] = useState({
    subject_id: '',
    date: format(new Date(), 'yyyy-MM-dd'),
    start_time: '09:00',
    end_time: '10:00',
    status: 'absent',
    notes: '',
  });
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: attendanceApi.addAdhoc,
    onSuccess: () => {
      queryClient.invalidateQueries(['calendar']);
      queryClient.invalidateQueries(['dashboard']);
      onClose();
      setFormData({
        subject_id: '',
        date: format(new Date(), 'yyyy-MM-dd'),
        start_time: '09:00',
        end_time: '10:00',
        status: 'absent',
        notes: '',
      });
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add Extra Class">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Select
          label="Subject"
          required
          value={formData.subject_id}
          onChange={(e) => setFormData({ ...formData, subject_id: e.target.value })}
          options={[
            { value: '', label: 'Select a subject' },
            ...subjects.map((s) => ({ value: s.id, label: s.name })),
          ]}
        />

        <Input
          label="Date"
          type="date"
          required
          value={formData.date}
          onChange={(e) => setFormData({ ...formData, date: e.target.value })}
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Start Time"
            type="time"
            required
            value={formData.start_time}
            onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
          />
          <Input
            label="End Time"
            type="time"
            required
            value={formData.end_time}
            onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
          />
        </div>

        <Select
          label="Status"
          value={formData.status}
          onChange={(e) => setFormData({ ...formData, status: e.target.value })}
          options={[
            { value: 'present', label: 'Present' },
            { value: 'absent', label: 'Absent' },
            { value: 'cancelled', label: 'Cancelled' },
          ]}
        />

        <Input
          label="Notes (Optional)"
          value={formData.notes}
          onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
          placeholder="Any additional notes..."
        />

        <div className="flex justify-end gap-3 pt-4">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={mutation.isPending}>
            Add Class
          </Button>
        </div>
      </form>
    </Modal>
  );
}
