export interface Channel {
  id: string;
  name?: string;
  url: string;
  is_online: boolean;
  resolution?: string;
  codec_video?: string;
  codec_audio?: string;
  screenshot_path?: string;
  [key: string]: unknown;
}
