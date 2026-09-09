import Purchases, { LOG_LEVEL } from 'react-native-purchases';
import { getRevenueCatConfig } from './revenuecat-config.mjs';
import { createRevenueCatService } from './revenuecat-service.mjs';

let service;

export function getRevenueCatService() {
  if (!service) {
    const config = getRevenueCatConfig(process.env);
    service = createRevenueCatService({ purchases: Purchases, config, logLevel: LOG_LEVEL.DEBUG });
  }
  return service;
}
