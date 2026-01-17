import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Edit2, Trash2, Clock, ChevronLeft, ChevronRight, CheckCircle, XCircle, MinusCircle } from 'lucide-react';
import { Card, Button, Badge, Modal, Input, Select, EmptyState, LoadingSpinner } from '../components/ui';
import { routineApi, routineEntryApi } from '../api/routine';
import { subjectApi } from '../api/academic';
import { attendanceApi } from '../api/attendance';
import { useSemester } from '../context/SemesterContext';
import { format, startOfWeek, addDays, addWeeks, subWeeks, isSameDay, isToday, isBefore, isAfter, parseISO, startOfDay } from 'date-fns';

const DAYS = [
  { value: 0, label: 'Mon' },
  { value: 1, label: 'Tue' },
  { value: 2, label: 'Wed' },
  { value: 3, label: 'Thu' },
  { value: 4, label: 'Fri' },
  { value: 5, label: 'Sat' },
  { value: 6, label: 'Sun' },
];

// Time slots from 10 AM to 6 PM (30-minute intervals = 16 slots)
const TIME_SLOTS = [
  { hour: 10, minute: 0, label: '10:00' },
  { hour: 10, minute: 30, label: '10:30' },
  { hour: 11, minute: 0, label: '11:00' },
  { hour: 11, minute: 30, label: '11:30' },
  { hour: 12, minute: 0, label: '12:00' },
  { hour: 12, minute: 30, label: '12:30' },
  { hour: 13, minute: 0, label: '1:00' },
  { hour: 13, minute: 30, label: '1:30' },
  { hour: 14, minute: 0, label: '2:00' },
  { hour: 14, minute: 30, label: '2:30' },
  { hour: 15, minute: 0, label: '3:00' },
  { hour: 15, minute: 30, label: '3:30' },
  { hour: 16, minute: 0, label: '4:00' },
  { hour: 16, minute: 30, label: '4:30' },
  { hour: 17, minute: 0, label: '5:00' },
  { hour: 17, minute: 30, label: '5:30' },
];

const NUM_SLOTS = TIME_SLOTS.length; // 16 slots

const SUBJECT_COLORS = [
  { base: 'bg-blue-100 border-blue-300 text-blue-800', present: 'bg-green-100 border-green-400', absent: 'bg-red-100 border-red-400', cancelled: 'bg-yellow-100 border-yellow-400' },
  { base: 'bg-purple-100 border-purple-300 text-purple-800', present: 'bg-green-100 border-green-400', absent: 'bg-red-100 border-red-400', cancelled: 'bg-yellow-100 border-yellow-400' },
  { base: 'bg-pink-100 border-pink-300 text-pink-800', present: 'bg-green-100 border-green-400', absent: 'bg-red-100 border-red-400', cancelled: 'bg-yellow-100 border-yellow-400' },
  { base: 'bg-orange-100 border-orange-300 text-orange-800', present: 'bg-green-100 border-green-400', absent: 'bg-red-100 border-red-400', cancelled: 'bg-yellow-100 border-yellow-400' },
  { base: 'bg-teal-100 border-teal-300 text-teal-800', present: 'bg-green-100 border-green-400', absent: 'bg-red-100 border-red-400', cancelled: 'bg-yellow-100 border-yellow-400' },
  { base: 'bg-indigo-100 border-indigo-300 text-indigo-800', present: 'bg-green-100 border-green-400', absent: 'bg-red-100 border-red-400', cancelled: 'bg-yellow-100 border-yellow-400' },
];

export default function RoutinePage() {
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null);
  const [currentWeekStart, setCurrentWeekStart] = useState(() => 
    startOfWeek(new Date(), { weekStartsOn: 1 }) // Monday as start
  );
  const { currentSemester } = useSemester();
  const queryClient = useQueryClient();

  // Get the dates for each day of the current week
  const weekDates = DAYS.map((_, index) => addDays(currentWeekStart, index));

  const { data: routines = [], isLoading: routinesLoading } = useQuery({
    queryKey: ['routines', currentSemester?.id],
    queryFn: () => routineApi.getBySemester(currentSemester?.id),
    enabled: !!currentSemester,
  });

  const routine = routines[0];

  const { data: entries = [], isLoading: entriesLoading } = useQuery({
    queryKey: ['routine-entries', routine?.id],
    queryFn: () => routineEntryApi.getAll(routine?.id),
    enabled: !!routine,
  });

  const { data: subjects = [] } = useQuery({
    queryKey: ['subjects', currentSemester?.id],
    queryFn: () => subjectApi.getAll(currentSemester?.id),
    enabled: !!currentSemester,
  });

  // Fetch attendance records for the current week
  const weekStartStr = format(currentWeekStart, 'yyyy-MM-dd');
  const weekEndStr = format(addDays(currentWeekStart, 6), 'yyyy-MM-dd');

  const { data: weekAttendance = [], refetch: refetchAttendance } = useQuery({
    queryKey: ['week-attendance', currentSemester?.id, weekStartStr],
    queryFn: () => attendanceApi.getAll({
      subject__semester: currentSemester?.id,
      date__gte: weekStartStr,
      date__lte: weekEndStr,
    }),
    enabled: !!currentSemester,
  });

  const createRoutineMutation = useMutation({
    mutationFn: routineApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['routines']);
    },
  });

  const deleteEntryMutation = useMutation({
    mutationFn: routineEntryApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['routine-entries']);
    },
  });

  // Generate classes for a specific date
  const generateMutation = useMutation({
    mutationFn: (date) => attendanceApi.generateForDate(currentSemester?.id, format(date, 'yyyy-MM-dd')),
    onSuccess: () => {
      refetchAttendance();
      queryClient.invalidateQueries(['week-attendance']);
    },
  });

  // Update attendance status
  const updateAttendanceMutation = useMutation({
    mutationFn: ({ id, status }) => attendanceApi.update(id, { status }),
    onSuccess: () => {
      refetchAttendance();
      queryClient.invalidateQueries(['week-attendance']);
      queryClient.invalidateQueries(['dashboard']);
    },
  });

  const isLoading = routinesLoading || entriesLoading;

  // Parse semester dates
  const semesterStartDate = currentSemester?.start_date ? parseISO(currentSemester.start_date) : null;
  const semesterEndDate = currentSemester?.end_date ? parseISO(currentSemester.end_date) : null;

  // Check if a date is within the semester range
  const isDateInSemester = (date) => {
    if (!semesterStartDate || !semesterEndDate) return false;
    const d = startOfDay(date);
    return !isBefore(d, startOfDay(semesterStartDate)) && !isAfter(d, startOfDay(semesterEndDate));
  };

  // Check if a date is in the past (before today)
  const isPastDate = (date) => {
    return isBefore(startOfDay(date), startOfDay(new Date()));
  };

  // Check if a date is today
  const isTodayDate = (date) => {
    return format(startOfDay(date), 'yyyy-MM-dd') === format(startOfDay(new Date()), 'yyyy-MM-dd');
  };

  // Check if a date is in the future (after today)
  const isFutureDate = (date) => {
    return isAfter(startOfDay(date), startOfDay(new Date()));
  };

  // Check if attendance can be marked for this date (must be in semester and not in future)
  const canMarkAttendance = (date) => {
    return isDateInSemester(date) && !isFutureDate(date);
  };

  // Create a map of subject to color index
  const subjectColorMap = {};
  subjects.forEach((subject, index) => {
    subjectColorMap[subject.id] = SUBJECT_COLORS[index % SUBJECT_COLORS.length];
  });

  // Find attendance record for a specific entry and date
  const findAttendanceRecord = (entry, date) => {
    const dateStr = format(date, 'yyyy-MM-dd');
    return weekAttendance.find(
      (a) => a.subject === entry.subject && 
             a.date === dateStr && 
             a.start_time?.slice(0, 5) === entry.start_time?.slice(0, 5)
    );
  };

  // Parse time string to total minutes since midnight
  const parseTimeToMinutes = (timeStr) => {
    if (!timeStr) return 0;
    const [hours, minutes] = timeStr.split(':').map(Number);
    return hours * 60 + (minutes || 0);
  };

  // Convert minutes to slot index (0 = 10:00, 1 = 10:30, etc.)
  const getSlotIndex = (timeStr) => {
    const minutes = parseTimeToMinutes(timeStr);
    const startMinutes = 10 * 60; // 10:00 AM in minutes
    const slotIndex = Math.floor((minutes - startMinutes) / 30);
    return Math.max(0, Math.min(slotIndex, NUM_SLOTS - 1));
  };

  // Get the number of slots a class should span
  const getColSpan = (startTime, endTime) => {
    const startSlot = getSlotIndex(startTime);
    const endMinutes = parseTimeToMinutes(endTime);
    const startMinutes = 10 * 60; // 10:00 AM
    const endSlot = Math.ceil((endMinutes - startMinutes) / 30);
    return Math.max(1, endSlot - startSlot);
  };

  // Get the starting column index for a class
  const getStartCol = (startTime) => {
    return getSlotIndex(startTime);
  };

  // Get entries for a specific day
  const getEntriesForDay = (dayValue) => {
    return entries
      .filter((e) => e.day_of_week === dayValue)
      .sort((a, b) => a.start_time.localeCompare(b.start_time));
  };

  // Build the timetable grid for a day
  const buildDayRow = (dayValue, date) => {
    const dayEntries = getEntriesForDay(dayValue);
    const cells = [];
    let currentCol = 0;

    const sortedEntries = [...dayEntries].sort((a, b) => 
      parseTimeToMinutes(a.start_time) - parseTimeToMinutes(b.start_time)
    );

    for (const entry of sortedEntries) {
      const startCol = getStartCol(entry.start_time);
      const colSpan = getColSpan(entry.start_time, entry.end_time);

      while (currentCol < startCol && currentCol < NUM_SLOTS) {
        cells.push({ type: 'empty', col: currentCol });
        currentCol++;
      }

      if (startCol >= 0 && startCol < NUM_SLOTS) {
        const attendanceRecord = findAttendanceRecord(entry, date);
        cells.push({
          type: 'entry',
          entry,
          colSpan: Math.min(colSpan, NUM_SLOTS - startCol),
          col: startCol,
          attendance: attendanceRecord,
          date,
        });
        currentCol = startCol + Math.min(colSpan, NUM_SLOTS - startCol);
      }
    }

    while (currentCol < NUM_SLOTS) {
      cells.push({ type: 'empty', col: currentCol });
      currentCol++;
    }

    return cells;
  };

  // Handle attendance toggle
  const handleAttendanceClick = async (cell) => {
    const { entry, attendance, date } = cell;
    
    // Don't allow marking if date is outside semester range
    if (!canMarkAttendance(date)) {
      return;
    }
    
    if (!attendance) {
      // Generate class first, then it will be marked as absent by default
      await generateMutation.mutateAsync(date);
      return;
    }

    // Cycle through statuses: absent -> present -> cancelled -> absent
    const statusCycle = { absent: 'present', present: 'cancelled', cancelled: 'absent' };
    const newStatus = statusCycle[attendance.status] || 'present';
    
    updateAttendanceMutation.mutate({ id: attendance.id, status: newStatus });
  };

  // Get status color class - past unmarked dates show as absent
  const getStatusColorClass = (attendance, subjectColor, date) => {
    // If attendance exists, use the actual status
    if (attendance) {
      switch (attendance.status) {
        case 'present': return 'bg-green-100 border-green-400 text-green-800';
        case 'absent': return 'bg-red-100 border-red-400 text-red-800';
        case 'cancelled': return 'bg-yellow-100 border-yellow-400 text-yellow-800';
        default: return subjectColor?.base || 'bg-gray-100 border-gray-300';
      }
    }
    
    // If no attendance record
    const inSemester = isDateInSemester(date);
    const isPast = isPastDate(date);
    const isFuture = isFutureDate(date);
    
    // If date is in the past and within semester, treat as absent
    if (isPast && inSemester) {
      return 'bg-red-100 border-red-400 text-red-800';
    }
    
    // If date is outside semester or in the future, show as disabled/gray
    if (!inSemester || isFuture) {
      return 'bg-gray-50 border-gray-200 text-gray-400 opacity-50';
    }
    
    // Today within semester - can be marked
    return subjectColor?.base || 'bg-gray-100 border-gray-300';
  };

  // Get status icon - past unmarked dates show absent icon
  const getStatusIcon = (status, attendance, date) => {
    // If attendance exists, show actual status icon
    if (attendance) {
      switch (status) {
        case 'present': return <CheckCircle className="h-3 w-3 text-green-600" />;
        case 'absent': return <XCircle className="h-3 w-3 text-red-600" />;
        case 'cancelled': return <MinusCircle className="h-3 w-3 text-yellow-600" />;
        default: return null;
      }
    }
    
    // If no attendance and past date within semester, show absent icon
    if (isPastDate(date) && isDateInSemester(date)) {
      return <XCircle className="h-3 w-3 text-red-600" />;
    }
    
    return null;
  };

  // Week navigation
  const goToPreviousWeek = () => setCurrentWeekStart(subWeeks(currentWeekStart, 1));
  const goToNextWeek = () => setCurrentWeekStart(addWeeks(currentWeekStart, 1));
  const goToCurrentWeek = () => setCurrentWeekStart(startOfWeek(new Date(), { weekStartsOn: 1 }));

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!routine && currentSemester) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Weekly Routine</h1>
          <p className="text-gray-600 mt-1">Set up your weekly class schedule</p>
        </div>
        <Card className="p-8">
          <EmptyState
            icon={Clock}
            title="No routine created"
            description="Create a weekly routine to automatically track your classes"
            action={
              <Button
                onClick={() => createRoutineMutation.mutate({ semester: currentSemester.id })}
                loading={createRoutineMutation.isPending}
              >
                <Plus className="h-4 w-4 mr-2" />
                Create Routine
              </Button>
            }
          />
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Weekly Routine</h1>
          <p className="text-gray-600 mt-1">
            {currentSemester?.name} • {entries.length} classes scheduled
          </p>
        </div>
        <Button onClick={() => setShowAddModal(true)} disabled={subjects.length === 0}>
          <Plus className="h-4 w-4 mr-2" />
          Add Class
        </Button>
      </div>

      {/* Week Navigation */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <button
            onClick={goToPreviousWeek}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <div className="text-center">
            <h2 className="text-lg font-semibold text-gray-900">
              {format(currentWeekStart, 'MMM d')} - {format(addDays(currentWeekStart, 6), 'MMM d, yyyy')}
            </h2>
            <button
              onClick={goToCurrentWeek}
              className="text-sm text-indigo-600 hover:text-indigo-700 mt-1"
            >
              Go to Current Week
            </button>
          </div>
          <button
            onClick={goToNextWeek}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      </Card>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-sm">
        <span className="text-gray-600 font-medium">Click on a class to mark attendance:</span>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-green-100 border-2 border-green-400" />
          <span className="text-gray-600">Present</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-red-100 border-2 border-red-400" />
          <span className="text-gray-600">Absent</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-yellow-100 border-2 border-yellow-400" />
          <span className="text-gray-600">Cancelled</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-gray-100 border-2 border-gray-300" />
          <span className="text-gray-600">Not marked</span>
        </div>
      </div>

      {subjects.length === 0 && (
        <Card className="p-4 bg-yellow-50 border-yellow-200">
          <p className="text-sm text-yellow-800">
            Please add some subjects first before adding classes to your routine.
          </p>
        </Card>
      )}

      {/* Timetable Grid */}
      <Card className="p-4 overflow-x-auto">
        <table className="w-full min-w-[1400px] border-collapse">
          <thead>
            <tr>
              <th className="w-24 p-1 text-left text-xs font-semibold text-gray-700 border-b-2 border-gray-200 sticky left-0 bg-white z-10">
                Day / Time
              </th>
              {TIME_SLOTS.map((slot, index) => (
                <th
                  key={`${slot.hour}-${slot.minute}`}
                  className="p-1 text-center text-xs font-semibold text-gray-700 border-b-2 border-gray-200 min-w-[70px]"
                >
                  {slot.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {DAYS.map((day, dayIndex) => {
              const date = weekDates[dayIndex];
              const cells = buildDayRow(day.value, date);
              const isTodayRow = isToday(date);
              const inSemester = isDateInSemester(date);
              
              return (
                <tr 
                  key={day.value} 
                  className={`border-b border-gray-100 ${isTodayRow ? 'bg-indigo-50' : !inSemester ? 'bg-gray-50 opacity-60' : 'hover:bg-gray-50'}`}
                >
                  <td className={`p-1 text-xs font-medium border-r border-gray-200 sticky left-0 z-10 ${isTodayRow ? 'bg-indigo-100' : !inSemester ? 'bg-gray-100' : 'bg-gray-50'}`}>
                    <div className={inSemester ? 'text-gray-900' : 'text-gray-400'}>{day.label}</div>
                    <div className={`text-xs ${isTodayRow ? 'text-indigo-600 font-semibold' : !inSemester ? 'text-gray-400' : 'text-gray-500'}`}>
                      {format(date, 'MMM d')}
                      {isTodayRow && <span className="ml-1">(Today)</span>}
                      {!inSemester && <span className="ml-1 text-red-400">(Out)</span>}
                    </div>
                  </td>
                  {cells.map((cell, index) => {
                    if (cell.type === 'empty') {
                      return (
                        <td
                          key={`${day.value}-${cell.col}`}
                          className="p-0.5 border-r border-gray-100 h-16"
                        />
                      );
                    }

                    if (cell.type === 'entry') {
                      const subjectColor = subjectColorMap[cell.entry.subject];
                      const colorClass = getStatusColorClass(cell.attendance, subjectColor, cell.date);
                      const subjectName = cell.entry.subject_name || subjects.find(s => s.id === cell.entry.subject)?.name;
                      const canMark = canMarkAttendance(cell.date);
                      const isPast = isPastDate(cell.date);
                      const inSemester = isDateInSemester(cell.date);
                      const isFuture = isFutureDate(cell.date);
                      
                      return (
                        <td
                          key={`${day.value}-${cell.entry.id}`}
                          colSpan={cell.colSpan}
                          className="p-0.5 h-16"
                        >
                          <div
                            className={`h-full p-1 rounded-lg border-2 ${colorClass} ${canMark ? 'cursor-pointer hover:shadow-md' : 'cursor-not-allowed'} transition-all group relative overflow-hidden`}
                            onClick={() => canMark && handleAttendanceClick(cell)}
                            title={!canMark ? (isFuture ? 'Cannot mark future dates' : 'Outside semester date range') : undefined}
                          >
                            <div className="flex flex-col h-full justify-between">
                              <div>
                                <div className="flex items-center justify-between">
                                  <p className="font-semibold text-[10px] leading-tight truncate flex-1">
                                    {subjectName}
                                  </p>
                                  {getStatusIcon(cell.attendance?.status, cell.attendance, cell.date)}
                                </div>
                                <p className="text-[9px] opacity-75">
                                  {cell.entry.start_time?.slice(0, 5)}-{cell.entry.end_time?.slice(0, 5)}
                                </p>
                              </div>
                              {cell.entry.room && cell.colSpan > 1 && (
                                <p className="text-[9px] opacity-60 truncate">
                                  {cell.entry.room}
                                </p>
                              )}
                              {!cell.attendance && inSemester && isTodayDate(cell.date) && cell.colSpan > 1 && (
                                <p className="text-[9px] opacity-50 italic">Click to mark</p>
                              )}
                              {!cell.attendance && isPast && inSemester && (
                                <p className="text-[9px] text-red-600 font-medium">Absent</p>
                              )}
                              {!inSemester && cell.colSpan > 1 && (
                                <p className="text-[9px] opacity-50 italic">Outside</p>
                              )}
                              {inSemester && isFutureDate(cell.date) && cell.colSpan > 1 && (
                                <p className="text-[9px] opacity-50 italic">Future</p>
                              )}
                            </div>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setEditingEntry(cell.entry);
                              }}
                              className="absolute top-0.5 right-0.5 p-0.5 rounded opacity-0 group-hover:opacity-100 hover:bg-white/50 transition-opacity"
                              title="Edit class"
                            >
                              <Edit2 className="h-2.5 w-2.5" />
                            </button>
                          </div>
                        </td>
                      );
                    }

                    return null;
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>

      {/* Subjects Legend */}
      {subjects.length > 0 && (
        <Card className="p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Subjects</h3>
          <div className="flex flex-wrap gap-2">
            {subjects.map((subject, index) => (
              <div
                key={subject.id}
                className={`px-3 py-1 rounded-full text-xs font-medium border ${SUBJECT_COLORS[index % SUBJECT_COLORS.length]?.base || 'bg-gray-100 border-gray-300'}`}
              >
                {subject.name}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Add/Edit Modal */}
      <RoutineEntryModal
        isOpen={showAddModal || !!editingEntry}
        onClose={() => {
          setShowAddModal(false);
          setEditingEntry(null);
        }}
        entry={editingEntry}
        routineId={routine?.id}
        subjects={subjects}
      />
    </div>
  );
}

function RoutineEntryModal({ isOpen, onClose, entry, routineId, subjects }) {
  const [formData, setFormData] = useState({
    subject: entry?.subject || '',
    day_of_week: entry?.day_of_week ?? 0,
    start_time: entry?.start_time?.slice(0, 5) || '10:00',
    end_time: entry?.end_time?.slice(0, 5) || '11:00',
    room: entry?.room || '',
    notes: entry?.notes || '',
    routine: routineId,
  });
  const queryClient = useQueryClient();

  // Reset form when modal opens or entry changes
  useEffect(() => {
    setFormData({
      subject: entry?.subject || '',
      day_of_week: entry?.day_of_week ?? 0,
      start_time: entry?.start_time?.slice(0, 5) || '10:00',
      end_time: entry?.end_time?.slice(0, 5) || '11:00',
      room: entry?.room || '',
      notes: entry?.notes || '',
      routine: routineId,
    });
  }, [entry, routineId, isOpen]);

  const mutation = useMutation({
    mutationFn: entry
      ? (data) => routineEntryApi.update(entry.id, data)
      : routineEntryApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['routine-entries']);
      onClose();
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate({ ...formData, routine: routineId });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={entry ? 'Edit Class' : 'Add Class'}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Select
          label="Subject"
          required
          value={formData.subject}
          onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
          options={[
            { value: '', label: 'Select a subject' },
            ...subjects.map((s) => ({ value: s.id, label: s.name })),
          ]}
        />

        <Select
          label="Day"
          value={formData.day_of_week}
          onChange={(e) => setFormData({ ...formData, day_of_week: parseInt(e.target.value) })}
          options={DAYS}
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

        <Input
          label="Room (Optional)"
          value={formData.room}
          onChange={(e) => setFormData({ ...formData, room: e.target.value })}
          placeholder="e.g., Room 101"
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
            {entry ? 'Save Changes' : 'Add Class'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
