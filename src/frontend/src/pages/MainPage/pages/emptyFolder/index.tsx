import ContentLogo from "@/assets/Content.svg?react";
import DotsPattern from "@/assets/Background_pattern_decorative.svg?react";
import { Button } from "@/components/ui/button";
import { useFolderStore } from "@/stores/foldersStore";
import useAddFlow from "@/hooks/flows/use-add-flow";
import { track } from "@/customization/utils/analytics";
import { useCustomNavigate } from "@/customization/hooks/use-custom-navigate";
import { useParams } from "react-router-dom";

type EmptyFolderProps = {
  setOpenModal: (open: boolean) => void;
};

export const EmptyFolder = ({ setOpenModal }: EmptyFolderProps) => {
  const folders = useFolderStore((state) => state.folders);
  const addFlow = useAddFlow();
  const navigate = useCustomNavigate();
  const { folderId } = useParams();

  return (
    <div className="relative flex h-full w-full items-center justify-center overflow-hidden">
      {/* Background with dots pattern */}
      <div className="absolute inset-0">
        <DotsPattern className="absolute left-1/2 top-[-264px] h-[768px] w-[768px] -translate-x-1/2 opacity-100" />
      </div>

      {/* Main content */}
      <div className="relative flex w-full max-w-[720px] flex-col items-center justify-center gap-8 px-6">
        {/* Logo */}
        <ContentLogo className="h-[60px] w-[60px]" />

        {/* Title and subtitle */}
        <div className="flex flex-col items-center gap-2">
          <h3
            className="text-xl font-semibold leading-7 text-[#101828]"
            data-testid="mainpage_title"
          >
            You're ready to start building
          </h3>
          <p className="text-center text-sm font-normal leading-5 text-[#475467]">
            This project doesn't have any flows yet. Start by creating a new one or explore templates to speed things up.
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-3">
          <Button
            variant="outline"

            onClick={() => setOpenModal(true)}
            className="h-10 rounded-lg border border-[#D0D5DD] bg-white px-4 py-2 text-sm font-semibold text-[#344054] hover:bg-[#F9FAFB] focus:ring-4 focus:ring-[#F2F4F7]"
          >
            Start with a Template
          </Button>
          <Button
            variant="default"
            onClick={() => {
              addFlow().then((id) => {
                navigate(
                  `/flow/${id}${folderId ? `/folder/${folderId}` : ""}`,
                );
              });
              track("New Flow Created", { template: "Blank Flow" });
            }}
            id="new-project-btn"
            data-testid="new_project_btn_empty_page"
            className="h-10 rounded-lg bg-[#0969DA] px-4 py-2 text-sm font-semibold text-white hover:bg-[#0156AA] focus:ring-4 focus:ring-[#D4DCFC] box-shadow-[0 1px 2px 0 rgba(16, 24, 40, 0.05)]"
          >
            Create Blank Flow
          </Button>
        </div>
      </div>
    </div>
  );
};

export default EmptyFolder;
