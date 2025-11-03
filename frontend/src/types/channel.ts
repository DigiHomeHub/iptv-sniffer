export interface Channel {
  id: string;
  name?: string;
  url: string;
  is_online: boolean;
  resolution?: string;
  codec_video?: string;
  codec_audio?: string;
  screenshot_path?: string;
  group?: string;
  tvg_id?: string;
  tvg_logo?: string;
  logo?: string;
  manually_edited?: boolean;
  [key: string]: unknown;
}
