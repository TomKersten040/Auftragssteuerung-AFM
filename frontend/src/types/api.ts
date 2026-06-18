export interface MotorEntry {
  id: number;
  motor_type: string;
  stator_number: string;
  status: 'iO' | 'niO' | 'wiO';
  entry_date: string;
  entry_time: string;
  storage_location: string;
  remarks: string | null;
  responsible_name: string;
  pickup_assigned_to: string | null;
  pickup_assigned_email: string | null;
  pickup_assigned_group: string | null;
  pickup_requested_by: string | null;
  pickup_requested_date: string | null;
  pickup_requested_time: string | null;
  pickup_request_comment: string | null;
  pickup_started_by: string | null;
  pickup_started_date: string | null;
  pickup_started_time: string | null;
  picked_up: 0 | 1;
  pickup_done_by: string | null;
  pickup_done_date: string | null;
  pickup_done_time: string | null;
  created_at: string;
  updated_at: string;
  pickup_status: 'Offen' | 'Angefordert' | 'In Bearbeitung' | 'Abgeholt' | 'Nicht erforderlich';
  mailto_url: string;
}

export interface Person {
  id: number;
  name: string;
  email: string | null;
  group_id: number | null;
  group_name: string | null;
}

export interface Group {
  id: number;
  name: string;
}

export interface Stats {
  total: number;
  io: number;
  open_nio: number;
  open_wio: number;
  my_open: number;
}

export interface LocationStat {
  storage_location: string;
  io_count: number;
  nio_count: number;
  wio_count: number;
  total: number;
}

export interface PageData {
  entries: MotorEntry[];
  stats: Stats;
  status_by_location: LocationStat[];
  request_persons: Person[];
  groups: Group[];
  motor_types: string[];
  storage_locations: string[];
  current_profile: string;
  current_view: string;
}

export interface NewEntryPayload {
  entry_date: string;
  entry_time: string;
  storage_location: string;
  remarks: string;
  pickup_request_comment: string;
  pickup_assigned_to: string;
  motors: { motor_type: string; stator_number: string; status: string }[];
}

export interface UpdateEntryPayload {
  motor_type: string;
  stator_number: string;
  status: string;
  entry_date: string;
  entry_time: string;
  storage_location: string;
  remarks: string;
  pickup_assigned_to: string;
  pickup_request_comment: string;
  picked_up: boolean;
  pickup_done_by: string;
  pickup_done_date: string;
  pickup_done_time: string;
}
