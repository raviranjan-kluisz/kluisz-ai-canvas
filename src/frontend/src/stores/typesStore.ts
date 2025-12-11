import { create } from "zustand";
import type { APIDataType } from "../types/api";
import type { TypesStoreType } from "../types/zustand/types";
import { enrichAllComponentsWithFeatureKeys } from "../utils/feature-enrichment";
import {
  extractSecretFieldsFromComponents,
  templatesGenerator,
  typesGenerator,
} from "../utils/reactflowUtils";

export const useTypesStore = create<TypesStoreType>((set, get) => ({
  ComponentFields: new Set(),
  setComponentFields: (fields) => {
    set({ ComponentFields: fields });
  },
  addComponentField: (field) => {
    set({ ComponentFields: get().ComponentFields.add(field) });
  },
  types: {},
  templates: {},
  data: {},
  setTypes: (data: APIDataType) => {
    // Enrich components with feature_key metadata for automatic filtering
    const enrichedData = enrichAllComponentsWithFeatureKeys(data);
    set((old) => ({
      types: typesGenerator(enrichedData),
      data: { ...old.data, ...enrichedData },
      ComponentFields: extractSecretFieldsFromComponents({
        ...old.data,
        ...enrichedData,
      }),
      templates: templatesGenerator(enrichedData),
    }));
  },
  setTemplates: (newState: {}) => {
    set({ templates: newState });
  },
  setData: (change: APIDataType | ((old: APIDataType) => APIDataType)) => {
    const newChange =
      typeof change === "function" ? change(get().data) : change;
    // Enrich components with feature_key metadata
    const enrichedData = enrichAllComponentsWithFeatureKeys(newChange);
    set({ data: enrichedData });
    get().setComponentFields(extractSecretFieldsFromComponents(enrichedData));
  },
}));
