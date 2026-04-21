import { FlutterEngine } from '@ohos/flutter_ohos';
import Docs2MCPPlugin from '../components/plugin/Docs2MCPPlugin';

export default class Docs2MCPRegistrant {
  static registerWith(flutterEngine: FlutterEngine): void {
    try {
      flutterEngine.getPlugins()?.add(new Docs2MCPPlugin());
    } catch (e) {
      console.error('Failed to register Docs2MCPPlugin:', e);
    }
  }
}
