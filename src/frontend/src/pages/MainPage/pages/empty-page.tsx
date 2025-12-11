import { useParams } from "react-router-dom";
import ContentLogo from "@/assets/Content.svg?react";
import DotsPattern from "@/assets/Background_pattern_decorative.svg?react";
import { ForwardedIconComponent } from "@/components/common/genericIconComponent";
import { Button } from "@/components/ui/button";
import { useCustomNavigate } from "@/customization/hooks/use-custom-navigate";
import { track } from "@/customization/utils/analytics";
import useAddFlow from "@/hooks/flows/use-add-flow";
import useFlowsManagerStore from "@/stores/flowsManagerStore";

export const EmptyPageCommunity = ({
  setOpenModal,
}: {
  setOpenModal: (open: boolean) => void;
}) => {
  const addFlow = useAddFlow();
  const navigate = useCustomNavigate();
  const { folderId } = useParams();
  const examples = useFlowsManagerStore((state) => state.examples);

  // Get first 3 examples for display
  const displayedExamples = examples.slice(3, 6);

  const handleCreateBlankFlow = () => {
    addFlow().then((id) => {
      navigate(`/flow/${id}${folderId ? `/folder/${folderId}` : ""}`);
    });
    track("New Flow Created", { template: "Blank Flow" });
  };

  const handleTemplateClick = (example: any) => {
    addFlow({ flow: example }).then((id) => {
      navigate(`/flow/${id}${folderId ? `/folder/${folderId}` : ""}`);
    });
    track("New Flow Created", { template: `${example.name} Template` });
  };

  return (
    <div className="relative flex h-full w-full items-center justify-center overflow-hidden bg-white">
      {/* Background with dots pattern */}
      <div className="absolute inset-0">
        <DotsPattern className="absolute left-1/2 top-[-264px] h-[768px] w-[768px] -translate-x-1/2 opacity-100" />
      </div>

      {/* Main content */}
      <div className="relative flex w-full max-w-[1200px] flex-col items-center justify-center gap-8 px-6 py-12">
        {/* Logo */}
        <ContentLogo className="h-[60px] w-[60px]" data-testid="empty_page_logo" />

        {/* Title and subtitle */}
        <div className="flex flex-col items-center gap-3">
          <h1
            className="text-center text-[30px] font-semibold leading-[38px] text-[#101828]"
            data-testid="mainpage_title"
          >
            Create flows, automate tasks, move faster
          </h1>
          <p
            className="text-center text-base font-normal leading-6 text-[#475467]"
            data-testid="empty_page_description"
          >
            Start with a blank canvas or browse ready-to-use templates designed for smart workflows
          </p>
        </div>

        {/* Create Blank Flow Button */}
        <Button
          onClick={handleCreateBlankFlow}
          id="new-project-btn"
          data-testid="new_project_btn_empty_page"
          className="h-11 rounded-lg bg-[#0969DA] px-6 py-2.5 text-base font-semibold text-white hover:bg-[#0856B3] focus:ring-4 focus:ring-[#D4DCFC]"
        >
          Create Blank Flow
        </Button>

        {/* OR Divider */}
        <div className="text-sm font-medium text-[#667085]">OR</div>

        {/* Start with a Template Section */}
        <div className="flex w-full items-center gap-4">
          <div className="flex-1 border-t border-[#EAECF0]"></div>
          <span className="text-sm font-medium text-[#667085]">Start with a Template</span>
          <div className="flex-1 border-t border-[#EAECF0]"></div>
        </div>

        {/* Template Cards */}
        {displayedExamples.length > 0 && (
          <div className="grid w-full max-w-[1000px] grid-cols-1 gap-4 md:grid-cols-3">
            {displayedExamples.map((example, index) => (
              <button
                key={index}
                onClick={() => handleTemplateClick(example)}
                className="group flex flex-col items-start gap-3 rounded-lg border border-[#EAECF0] bg-white p-6 text-left transition-all hover:border-[#D0D5DD] hover:shadow-sm"
              >
                {/* Icon */}
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#EAECF0] bg-[#F9FAFB]">
                  <ForwardedIconComponent
                    name="Workflow"
                    className="h-5 w-5 text-[#0969DA]"
                  />
                </div>

                {/* Title */}
                <h3 className="text-base font-semibold leading-6 text-[#101828]">
                  {example.name}
                </h3>

                {/* Description */}
                <p className="text-sm font-normal leading-5 text-[#475467]">
                  {example.description || "Create automated workflows and streamline your tasks efficiently."}
                </p>
              </button>
            ))}
          </div>
        )}

        {/* Explore more templates link */}
        <button
          onClick={() => setOpenModal(true)}
          className="group flex items-center gap-2 text-sm font-semibold text-[#0969DA] hover:text-[#0856B3]"
        >
          <span>Explore more templates</span>
          <ForwardedIconComponent
            name="ArrowRight"
            className="h-4 w-4 transition-transform group-hover:translate-x-1"
          />
        </button>
      </div>
    </div>
  );
};

export default EmptyPageCommunity;
