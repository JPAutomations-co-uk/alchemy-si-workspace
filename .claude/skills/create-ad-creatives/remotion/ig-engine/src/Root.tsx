import React from "react";
import { Composition, registerRoot } from "remotion";
import { IgEngine } from "./IgEngine";
import { FollowCTA } from "./FollowCTA";

const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="IgEngine"
        component={IgEngine}
        durationInFrames={1410}
        fps={30}
        width={3840}
        height={2160}
        defaultProps={{}}
      />
      <Composition
        id="FollowCTA"
        component={FollowCTA}
        durationInFrames={45}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          username: "jpautomations",
          displayName: "JP Automations",
        }}
      />
    </>
  );
};

registerRoot(RemotionRoot);
